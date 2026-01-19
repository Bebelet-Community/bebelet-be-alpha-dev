from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model


from apps.category.models import Category, Attribute, UsageRange
from apps.region.models import Region

from cloudinary.models import CloudinaryField

User = get_user_model()


class PublishStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PUBLISHED = "published", "Published"
    SOLD = "sold", "Sold"
    DEACTIVATED = "deactivated","Deactivated"

class SalePost(models.Model):
    post_id = models.IntegerField(unique=True,  help_text="6 digits unique post id") # 6 digits random num
    post_status = models.CharField(max_length=11, choices=PublishStatus.choices, default=PublishStatus.PENDING)
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, null=True)
    region = models.ForeignKey(Region, on_delete=models.DO_NOTHING, null=True)
    post_title = models.CharField(max_length=70)
    description = models.TextField() 
    product_price = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    posted_at = models.DateTimeField(null=True, blank=True, default=timezone.now)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    min_usage = models.ForeignKey(UsageRange, on_delete=models.SET_NULL, null=True, blank=True, related_name='min_usage_range')
    max_usage = models.ForeignKey(UsageRange, on_delete=models.SET_NULL, null=True, blank=True, related_name='max_usage_range')
    viewed = models.IntegerField(default=0) # how many time the post is viewed

    def is_published(self):
        return self.post_status == PublishStatus.PUBLISHED
    
    def save(self, *args, **kwargs):
        if self.min_usage and self.max_usage and self.min_usage.unique_id > self.max_usage.unique_id:
            raise ValidationError("Minimum usage range must be less than or equal to maximum usage range.")
        super().save(*args, **kwargs)

    @property
    def effective_latitude(self):
        return self.latitude if self.latitude is not None else self.region.latitude
        
    @property
    def effective_longitude(self):
        return self.longitude if self.longitude is not None else self.region.longitude

    def __str__(self):
        return f"{self.post_id}"


class SalePostAttribute(models.Model):
    salepost = models.ForeignKey(SalePost, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=['salepost', 'attribute'], name="unique_salepost_attribute")
        ]


    def __str__(self):
        return f"{self.salepost.post_title} - {self.attribute.unique_name} - {self.value}"


class Image(models.Model):
    img = CloudinaryField("salepost_image", blank=True, null=True)
    related_post = models.ForeignKey(SalePost, on_delete=models.DO_NOTHING)

    @property
    def get_url(self):
        return f"https://res.cloudinary.com/{CLOUDINARY_CLOUD_NAME}/{self.img}" 