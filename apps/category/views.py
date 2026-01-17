from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.responses import build_response, swagger_response

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse

from .serializers import CategorySerializer, AttributeSerializer, AttributeChoiceSerializer, SubCategorySerializer

from .models import Category, Attribute, AttributeChoice

class CategoryListView(APIView):
    permission_classes = []

    @extend_schema(
        summary = "Category List",
        description = "Getting category list",
        tags = ["Category"],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = True,
                description = "Getting category list",
                examples = [
                    swagger_response(
                        name = "Categories retrieved successfully",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Categories retrieved successfully",
                        data = [
                            {
                                "id": 1,
                                "parent": None,
                                "name": "Category-1",
                                "additional_info": "",
                                "icon_url": None,
                                "subcategories": None
                            },
                            {
                                "id": 2,
                                "parent": None,
                                "name": "Category-2",
                                "additional_info": "",
                                "icon_url": None,
                                "subcategories": [
                                    {
                                        "id": 3,
                                        "parent": 2,
                                        "name": "Category-3",
                                        "additional_info": "",
                                        "icon_url": None,
                                        "subcategories": None
                                    }
                                ]
                            }
                        ]
                    ),
                ]
            ),
        }
    )
    def get(self, request):
        category_list = Category.objects.filter(parent=None)
        payload = build_response(
            success = True,
            code = status.HTTP_200_OK,
            message = "Categories retrieved successfully",
            data = CategorySerializer(category_list, many=True).data
        )

        return Response(payload, status=status.HTTP_200_OK)

class CategoryView(APIView):
    permission_classes = []


    @extend_schema(
        summary = "Category Info",
        description = "Getting category info",
        tags = ["Category"],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = True,
                description = "Getting category info",
                examples = [
                    swagger_response(
                        name = "Category retrieved successfully",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Category retrieved successfully",
                        data = {
                            "id": 1,
                            "parent": None,
                            "name": "Test",
                            "additional_info": "",
                            "icon_url": None,
                            "subcategories": None,
                            "usage_range": None,
                            "attributes": None,
                            "brands": None
                        }
                    ),
                ]
            ),
        }
    )

    def get(self, request, id):
        try:
            category_instance = Category.objects.get(pk=id)
            serializers = SubCategorySerializer(category_instance)
            payload = build_response(
                success=True,
                code = status.HTTP_200_OK,
                message = "Category retrieved successfully",
                data = serializers.data
            )
            return Response(payload, status.HTTP_200_OK)

        except Category.DoesNotExist:
            payload = build_response(
                success=False,
                code=status.HTTP_404_NOT_FOUND,
                message="Category not found",
            )
            return Response(payload, status=status.HTTP_404_NOT_FOUND)
