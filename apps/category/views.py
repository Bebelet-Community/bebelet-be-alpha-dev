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
        description = "List top-level categories (and nested subcategories).",
        tags = ["Category"],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = True,
                description = "Categories retrieved.",
                examples = [
                    swagger_response(
                        name = "Categories retrieved successfully",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Categories retrieved successfully.",
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
            message = "Categories retrieved successfully.",
            data = CategorySerializer(category_list, many=True).data
        )

        return Response(payload, status=status.HTTP_200_OK)

class CategoryView(APIView):
    permission_classes = []


    @extend_schema(
        summary = "Retrieve category",
        description = "Retrieve category details by ID.",
        tags = ["Category"],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = SubCategorySerializer,
                description = "Category retrieved.",
                examples = [
                    swagger_response(
                        name = "Category retrieved successfully",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Category retrieved successfully.",
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
            status.HTTP_404_NOT_FOUND : OpenApiResponse(
                response = False,
                description = "Category not found.",
                examples = [
                    swagger_response(
                        name="Category not found.",
                        success=False,
                        code=status.HTTP_404_NOT_FOUND,
                        message="Category not found.",
                        data={}
                    )
                ]
            )
        }
    )

    def get(self, request, category_id):
        try:
            category_instance = Category.objects.get(pk=category_id)
            serializers = SubCategorySerializer(category_instance)
            payload = build_response(
                success=True,
                code = status.HTTP_200_OK,
                message = "Category retrieved successfully.",
                data = serializers.data
            )
            return Response(payload, status.HTTP_200_OK)

        except Category.DoesNotExist:
            payload = build_response(
                success=False,
                code=status.HTTP_404_NOT_FOUND,
                message="Category not found.",
            )
            return Response(payload, status=status.HTTP_404_NOT_FOUND)


class AttributeListView(APIView):
    permission_classes = []

    @extend_schema(
        summary = "List attributes",
        description = "List all attributes.",
        tags = ["Category"],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = AttributeSerializer,
                description = "Attributes retrieved.",
                examples = [
                    swagger_response(
                        name = "Attributes retrieved successfully",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Attributes retrieved successfully.",
                        data = [
                            {
                                "id": 1,
                                "unique_name": "attribute1",
                                "display_name": "Attribute1",
                                "data_type": "number",
                                "is_required": True,
                                "choices": None
                            }
                        ]
                    ),
                ]
            ),
        }
    )
    def get(self, request):
        attribute_list = Attribute.objects.all()
        payload = build_response(
            success=True,
            code=status.HTTP_200_OK,
            message = "Attributes retrieved successfully",
            data = AttributeSerializer(attribute_list, many=True).data
        )

        return Response(payload, status=status.HTTP_200_OK)

    


class AttributeView(APIView):
    permission_classes = []

    @extend_schema(
        summary = "Retrieve attribute",
        description = "Retrieve attribute details by ID.",
        tags = ["Category"],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = AttributeSerializer,
                description = "Attribute retrieved.",
                examples = [
                    swagger_response(
                        name = "Attribute retrieved",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Attribute retrieved.",
                        data = {
                            "id": 1,
                            "unique_name": "test",
                            "display_name": "Test",
                            "data_type": "number",
                            "is_required": True,
                            "choices": None
                        }
                    ),
                ]
            ),
            status.HTTP_404_NOT_FOUND : OpenApiResponse(
                response = False,
                description = "Attribute not found.",
                examples = [
                    swagger_response(
                        name="Attribute not found",
                        success=False,
                        code=status.HTTP_404_NOT_FOUND,
                        message="Attribute not found.",
                        data=None
                    )
                ]
            )
        }
    )
    def get(self, request, attribute_id):
        try:
            attribute_instance = Attribute.objects.get(pk=attribute_id)
            payload = build_response(
                success = True,
                code=status.HTTP_200_OK,
                message="Attribute retrieved successfully.",
                data = AttributeSerializer(attribute_instance).data
            )
            return Response(payload, status=status.HTTP_200_OK)
        except Attribute.DoesNotExist:
            payload = build_response(
                success = False,
                code=status.HTTP_404_NOT_FOUND,
                message="Attribute not found."
            )
            return Response(payload, status=status.HTTP_404_NOT_FOUND)


class AttributeChoiceListView(APIView):
    permission_classes = []

    @extend_schema(
        summary = "List attribute choices",
        description = "List all attribute choices.",
        tags = ["Category"],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = AttributeChoiceSerializer,
                description = "Attribute choices retrieved.",
                examples = [
                    swagger_response(
                        name = "Attribute choices retrieved successfully",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Attribute choices retrieved successfully.",
                        data = [
                            {
                                "id": 1,
                                "attribute": 1,
                                "value": "Choice1"
                            }
                        ]
                    ),
                ]
            ),
        }
    )
    def get(self, request):
        attributechoice_list = AttributeChoice.objects.all()
        payload = build_response(
            success=True,
            code=status.HTTP_200_OK,
            message = "Attribute choices retrieved successfully.",
            data = AttributeChoiceSerializer(attributechoice_list, many=True).data
        )

        return Response(payload, status=status.HTTP_200_OK)


class AttributeChoiceView(APIView):
    permission_classes = []

    @extend_schema(
        summary = "Retrieve attribute choice",
        description = "Retrieve attribute choice details by ID.",
        tags = ["Category"],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = AttributeChoiceSerializer,
                description = "Attribute choice retrieved.",
                examples = [
                    swagger_response(
                        name = "Attribute choice retrieved successfully",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Attribute choice retrieved successfully.",
                        data = {
                            "id": 1,
                            "attribute": 1,
                            "value": "Choice1"
                        }
                    ),
                ]
            ),
            status.HTTP_404_NOT_FOUND : OpenApiResponse(
                response = False,
                description = "Attribute choice not found.",
                examples = [
                    swagger_response(
                        name="Attribute choice not found",
                        success=False,
                        code=status.HTTP_404_NOT_FOUND,
                        message="Attribute choice not found.",
                        data=None
                    )
                ]
            )
        }
    )
    def get(self, request, attribute_choice_id):
        try:
            attributeChoice_instance = AttributeChoice.objects.get(pk=attribute_choice_id)
            payload = build_response(
                success = True,
                code=status.HTTP_200_OK,
                message="Attribute choice retrieved successfully",
                data = AttributeChoiceSerializer(attributeChoice_instance).data
            )
            return Response(payload, status=status.HTTP_200_OK)
        except AttributeChoice.DoesNotExist:
            payload = build_response(
                success = False,
                code=status.HTTP_404_NOT_FOUND,
                message="Attribute choice not found."
            )
            return Response(payload, status=status.HTTP_404_NOT_FOUND)