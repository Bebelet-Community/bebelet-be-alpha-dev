from django.conf import settings

from rest_framework import serializers

from apps.salepost.models import SalePost, SalePostAttribute, Image
from apps.category.models import Attribute,AttributeChoice


def get_max_images_per_salepost():
    return int(settings("MAX_NUM_OF_IMAGES_PER_SALEPOST", 5))

class SalePostAttributeSerializer(serializers.ModelSerializer):
    attribute = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()

    class Meta:
        model = SalePostAttribute
        fields = ['attribute', 'value']

    def get_attribute(self, obj):
        attribute = Attribute.objects.get(id=obj.attribute.id)
        return attribute.unique_name
    def get_value(self, obj):
        attribute = Attribute.objects.get(id=obj.attribute.id)
        if attribute.data_type == 'choice':
            try:
                choice = AttributeChoice.objects.get(id=int(obj.value))
                return choice.value
            except AttributeChoice.DoesNotExist:
                return None
        elif attribute.data_type == 'number':
            return int(obj.value)
        else:
            return obj.value


class SalePostListSerializer(serializers.Serializer):
    post_id = serializers.IntegerField(required=False, help_text="6 digits unique post id")
    post_status = serializers.CharField(required=False)
    seller = serializers.CharField(required=True)
    category = serializers.CharField(required=True)
    region = serializers.CharField(required=True)
    post_title = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    posted_at = serializers.DateTimeField(required=False)
    viewed = serializers.IntegerField(required=False)
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)
    product_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    attributes = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    def get_attributes(self, obj):
        attributes = SalePostAttribute.objects.filter(salepost=obj)
        if attributes.exists():
            return SalePostAttributeSerializer(attributes, many=True).data
        return None
    
    def get_images(self, obj):
        images = Image.objects.filter(related_post=obj)
        if images.exists():
            return ImageSerializer(images, many=True).data
        return None


class SalePostCreateSerializer(serializers.Serializer):
    category = serializers.IntegerField(required=True)
    region = serializers.IntegerField(required=True)
    post_title = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    product_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)
    min_usage_range = serializers.IntegerField(required=False)
    max_usage_range = serializers.IntegerField(required=False)

class SalePostUpdateSerializer(serializers.Serializer):
    post_title = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    product_price = serializers.DecimalField(max_digits=10, decimal_places=2)


class ImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ['id', 'image_url']

    def get_image_url(self, obj):
        return obj.get_url  

class MultipleImageUploadSerializer(serializers.Serializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True
    )
    post_id = serializers.IntegerField(write_only=True)

    def validate(self, data):
        images = data.get('images', [])
        post_id = data.get('post_id')
        try:
            salepost = SalePost.objects.get(post_id=post_id)
        except SalePost.DoesNotExist:
            raise serializers.ValidationError({"post_id": "SalePost with this post_id does not exist."})

        existing_count = Image.objects.filter(related_post=salepost).count()
        max_images = get_max_images_per_salepost()
        remaining_slots = max_images - existing_count

        if len(images) > remaining_slots:
            raise serializers.ValidationError({
                "images": f"Only {remaining_slots} more image(s) can be uploaded. This post already has {existing_count} images."
            })
        return data

    def create(self, validated_data):
        images = validated_data.pop('images', [])
        post_id = validated_data.pop('post_id')  # This is already a SalePost object from validate_post_id
        related_post = SalePost.objects.get(post_id=post_id)
        image_instances = [Image.objects.create(img=image, related_post=related_post) for image in images]
        return image_instances