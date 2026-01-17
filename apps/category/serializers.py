from rest_framework import serializers
from .models import Category, Attribute, AttributeChoice, Brand, UsageRange

class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'parent', 'name', 'additional_info', 'icon_url', 'subcategories']

    def get_subcategories(self, obj):
        subcategories = Category.objects.filter(parent=obj)
        if subcategories.exists():
            return CategorySerializer(subcategories, many=True).data
        return None
    
class SubCategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    brands = serializers.SerializerMethodField()
    usage_range = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'parent', 'name', 'additional_info', 'icon_url', 'subcategories', 'usage_range',  'attributes', 'brands']

    def get_subcategories(self, obj):
        subcategories = Category.objects.filter(parent=obj)
        if subcategories.exists():
            return SubCategorySerializer(subcategories, many=True).data
        return None
    
    def get_attributes(self, obj):
        attributes = Attribute.objects.filter(categories=obj)
        if attributes.exists():
            serializer_data = AttributeSerializer(attributes, many=True).data
            return serializer_data
        
    def get_brands(self, obj):
        brands = obj.brands.filter(category=obj)
        if brands.exists():
            return BrandSerializer(brands, many=True).data
        return None
    
    def get_usage_range(self, obj):
        if obj.min_usage_range and obj.max_usage_range:
            usage_range_list = UsageRange.objects.filter(unique_id__gte=obj.min_usage_range.unique_id, unique_id__lte=obj.max_usage_range.unique_id)
            return UsageRangeSerializer(usage_range_list, many=True).data
        elif obj.min_usage_range:
            usage_range_list = UsageRange.objects.filter(unique_id__gte=obj.min_usage_range.unique_id)
            return UsageRangeSerializer(usage_range_list, many=True).data
        elif obj.max_usage_range:
            usage_range_list = UsageRange.objects.filter(unique_id__lte=obj.max_usage_range.unique_id)
            return UsageRangeSerializer(usage_range_list, many=True).data
        else:
            return None

class UsageRangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageRange
        fields = ['id', 'name']    

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name']


class AttributeSerializer(serializers.ModelSerializer):
    choices = serializers.SerializerMethodField()

    class Meta:
        model = Attribute
        fields = ['id', 'unique_name', 'display_name', 'data_type', 'is_required', 'choices']

    def get_choices(self, obj):
        if obj.data_type == 'choice':
            choices = AttributeChoice.objects.filter(attribute=obj)
            if choices.exists():
                return AttributeChoiceSerializer(choices, many=True).data
        return None

class AttributeChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeChoice
        fields = ['id', 'attribute', 'value']