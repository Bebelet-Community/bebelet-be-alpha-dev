from rest_framework import serializers
from .models import Region

class RegionListSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    name = serializers.CharField(required=True)
    parent = serializers.CharField(required=True)
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)

class RegionCreateSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    parent = serializers.CharField(required=False)

class RegionUpdateSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    name = serializers.CharField(required=False)
    parent = serializers.CharField(required=False)
    

class RegionTreeSerializer(serializers.ModelSerializer):
    subregions = serializers.SerializerMethodField()

    class Meta:
        model = Region
        fields = ['id', 'name', 'parent', 'subregions']
    def get_subregions(self, obj):
        subcategories = Region.objects.filter(parent=obj)
        if subcategories:
            return RegionTreeSerializer(subcategories, many=True).data
        return None
    
# only for il ve ilçe
class RegionListTreeSerializer(serializers.ModelSerializer):
    subregions = serializers.SerializerMethodField()

    class Meta:
        model = Region
        fields = ['id', 'name', 'subregions']

    def get_subregions(self, obj):
        children = Region.objects.filter(parent=obj)
        return [{'id': child.id, 'name': child.name} for child in children]