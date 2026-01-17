from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
import uuid
import os

def get_category_icon_path(instance, filename):
    ext = filename.split(".")[-1]
    unique_id = uuid.uuid4().hex[:6]
    filename = f"{slugify(instance.name)}-{unique_id}.{ext}"
    return os.path.join('category_icons', filename)


class DataType(models.TextChoices):
    TEXT = "text", 'Text'
    NUMBER = "number", 'Number'
    CHOICE = "choice", 'Choice'
    SWITCH = "switch", 'Switch'


class Category(models.Model):
    name = models.CharField(unique=True, max_length=100)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name="subcategories")
    icon = models.FileField(upload_to=get_category_icon_path, null=True, blank=True)
    additional_info = models.TextField(blank=True, null=True)
    min_usage_range = models.ForeignKey('UsageRange', on_delete=models.SET_NULL, null=True, blank=True, related_name='categories')
    max_usage_range = models.ForeignKey('UsageRange', on_delete=models.SET_NULL, null=True, blank=True, related_name='max_categories')


    def __str__(self):
        return self.name

    def is_root_category(self):
        return self.parent is None

    def save(self, *args, **kwargs):
        if self.min_usage_range and self.max_usage_range and self.min_usage_range.unique_id > self.max_usage_range.unique_id:
            raise ValidationError("Minimum usage range must be less than or equal to maximum usage range.")
        super().save(*args, **kwargs)

    @property
    def icon_url(self):
        if self.icon:
            return self.icon.url
        return None
    
class UsageRange(models.Model):
    unique_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.ManyToManyField(Category, related_name='brands', blank=True)

    def __str__(self):
        return self.name

class Attribute(models.Model):
    unique_name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)
    data_type = models.CharField(max_length=20, choices=DataType.choices, default=DataType.CHOICE)
    categories = models.ManyToManyField(Category, related_name='attributes', blank=True)
    is_required = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.display_name} - {self.unique_name}"
    
    def clean(self):
        existing_attributes = Attribute.objects.filter(unique_name__iexact=self.unique_name).exclude(id=self.pk)
        if existing_attributes.exists():
            raise ValidationError(f"An attribute with the unique name '{self.unique_name}' already exists.")
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class AttributeChoice(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='choices')
    value = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.attribute.display_name}: {self.value}"
    
    def clean(self):
        if self.attribute.data_type not in [DataType.CHOICE, DataType.SWITCH]:
            raise ValidationError("Attribute must be of type 'Choice' or 'Switch' to have choices.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)    

    class Meta:
        unique_together = ('attribute', 'value')