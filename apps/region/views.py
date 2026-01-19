from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from core.responses import build_response, swagger_response
from core.permissions import HasPerm
from core.text import turkish_lower

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse

from .serializers import RegionListSerializer, RegionCreateSerializer, RegionUpdateSerializer,RegionTreeSerializer, RegionListTreeSerializer

from . models import Region


class RegionViewSet(ModelViewSet):
    queryset = Region.objects.filter(parent=None)
    serializer_class = RegionTreeSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), HasPerm("region.add_region")]
        elif self.action == "update":
            return [IsAuthenticated(), HasPerm("region.change_region")]
        elif self.action == "destroy":
            return [IsAuthenticated(), HasPerm("region.delete_region")]
        else:
            return []


    #List Endpoint
    @extend_schema(
        summary = "Region List",
        description = "List top-level regions (and nested subregions).",
        tags = ["Region"],
        parameters = [
            OpenApiParameter(
                name="keyword",
                required=False,
                type=OpenApiTypes.STR,
                description="Filter regions by keyword.",
            )
        ],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response=True,
                description = "Regions retrieved.",
                examples = [
                    swagger_response(
                        name = "Regions retrieved successfully",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Regions retrieved successfully.",
                        data = [
                            {
                                "id": 1,
                                "name": "Region",
                                "subregions": [
                                    {
                                        "id": 3,
                                        "name": "Region2"
                                    }
                                ]
                            },
                            {
                                "id": 2,
                                "name": "Region1",
                                "subregions": []
                            }
                        ]
                    ),
                    swagger_response(
                        name = "Regions retrieved successfully with keyword",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Regions retrieved successfully.",
                        data = [
                            {
                                "id": 3,
                                "name": "Region2",
                                "full_path": "Region / Region2",
                                "level": "ilce"
                            }
                        ]
                    ),
                ]
            ),
            status.HTTP_404_NOT_FOUND :  OpenApiResponse(
                response=True,
                description = "No regions matched the given keyword.",
                examples = [
                    swagger_response(
                        name = "Regions not found",
                        success = False,
                        code = status.HTTP_404_NOT_FOUND,
                        message = "Regions not found."
                    )
                ]                
            )
        }
    )
    def list(self, request):
        keyword = request.query_params.get('keyword', '').strip()

        if keyword:
            normalized_keyword = turkish_lower(keyword)
            results = []

            all_regions = Region.objects.select_related('parent__parent')

            for region in all_regions:
                name_normalized = turkish_lower(region.name)

                if name_normalized.startswith(normalized_keyword):
                    # Mahalle: has parent (ilçe), and grandparent (il)
                    if region.parent and region.parent.parent:
                        ilce = region.parent
                        il = ilce.parent
                        results.append({
                            'id': region.id,
                            'name': region.name,
                            'full_path': f"{il.name} / {ilce.name} / {region.name}",
                            'level': 'mahalle'
                        })
                    # İlçe: has parent (il), but no grandparent
                    elif region.parent and not region.parent.parent:
                        il = region.parent
                        results.append({
                            'id': region.id,
                            'name': region.name,
                            'full_path': f"{il.name} / {region.name}",
                            'level': 'ilce'
                        })
                        # fetch mahalleler of this ilçe
                        mahalleler = Region.objects.filter(parent=region)
                        for mahalle in mahalleler:
                            results.append({
                                'id': mahalle.id,
                                'name': mahalle.name,
                                'full_path': f"{il.name} / {region.name} / {mahalle.name}",
                                'level': 'mahalle'
                            })
                    # İl: no parent
                    elif not region.parent:
                        ilceler = Region.objects.filter(parent=region)
                        for ilce in ilceler:
                            results.append({
                                'id': ilce.id,
                                'name': ilce.name,
                                'full_path': f"{region.name} / {ilce.name}",
                                'level': 'ilce'
                            })

            if results:
                payload = build_response(
                    success=True,
                    message="Regions retrieved successfully.",
                    code=status.HTTP_200_OK,
                    data = results
                )
                return Response(payload, status=status.HTTP_200_OK)
            else:
                payload = build_response(
                    success=False,
                    message="Regions not found.",
                    code=status.HTTP_404_NOT_FOUND,
                )
                return Response(payload, status=status.HTTP_404_NOT_FOUND)

        # Ana istek (keyword yoksa): sadece illeri dön
        parent_regions = self.get_queryset()
        serializer = RegionListTreeSerializer(parent_regions, many=True)
        payload = build_response(
            success=True,
            code=status.HTTP_200_OK,
            message="Regions retrieved successfully.",
            data = serializer.data
        )
        return Response(payload, status=status.HTTP_200_OK)


    #Retrive Endpoint
    @extend_schema(
        summary = "Retrieve region",
        description = "Retrieve region details by ID.",
        tags = ["Region"],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = RegionTreeSerializer,
                description = "Region retrieved.",
                examples = [
                    swagger_response(
                        name = "Region retrieved successfully",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Region retrieved successfully.",
                        data = {
                            "id": 1,
                            "name": "Region",
                            "parent": None,
                            "subregions": [
                                {
                                    "id": 3,
                                    "name": "Region2",
                                    "parent": 1,
                                    "subregions": None
                                }
                            ]
                        }
                    ),
                ]
            ),
            status.HTTP_404_NOT_FOUND :  OpenApiResponse(
                response=True,
                description="Region not found.",
                examples=[
                    swagger_response(
                        name = "Region not found",
                        success = False,
                        code = status.HTTP_404_NOT_FOUND,
                        message = "Region not found."
                    )
                ]                
            )
        }
    )
    def retrieve(self, request, pk=None):
        try:
            region_instance = Region.objects.get(id=pk)
            serializer = RegionTreeSerializer(region_instance)
            payload = build_response(
                success=True,
                code=status.HTTP_200_OK,
                message="Region retrieved successfully.",
                data=serializer.data
            )
            return Response(payload, status=status.HTTP_200_OK)
        except Region.DoesNotExist:
            payload = build_response(
                success=False,
                code=status.HTTP_404_NOT_FOUND,
                message="Region not found."
            )
            return Response(payload, status=status.HTTP_404_NOT_FOUND)



    #Create Endpoint
    @extend_schema(
        summary="Create region",
        description="Create a new region. If parent is provided, the region will be created as a child region.",
        tags=["Region"],
        auth=[{"cookieAuth": []}],
        parameters=[
            OpenApiParameter(
                name="name",
                required=True,
                type=OpenApiTypes.STR,
                description="Region name.",
            ),
            OpenApiParameter(
                name="parent",
                required=False,
                type=OpenApiTypes.INT,
                description="Parent region ID (optional).",
            ),
        ],
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=True,
                description="Region created.",
                examples=[
                    swagger_response(
                        name="Root region created successfully",
                        success=True,
                        code=status.HTTP_201_CREATED,
                        message="Region3 has been created as a root region.",
                        data={},
                    ),
                    swagger_response(
                        name="Child region created successfully",
                        success=True,
                        code=status.HTTP_201_CREATED,
                        message="Region3 has been created as a child to Region2.",
                        data={},
                    ),
                ],
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=True,
                description="Validation error (missing name or invalid parent).",
                examples=[
                    swagger_response(
                        name="Name is required",
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="Name is required.",
                        data={},
                    ),
                    swagger_response(
                        name="Invalid parent region",
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="1 is not a valid parent, please select an existing parent region.",
                        data={},
                    ),
                ],
            ),
            status.HTTP_406_NOT_ACCEPTABLE: OpenApiResponse(
                response=True,
                description="Region already exists.",
                examples=[
                    swagger_response(
                        name="Region already exists",
                        success=False,
                        code=status.HTTP_406_NOT_ACCEPTABLE,
                        message="Region already exists.",
                        data={},
                    ),
                ],
            ),
        },
    )

    def create(self, request):
        region_name = request.data.get('name')
        parent_region = request.data.get('parent')

        if region_name:
            if parent_region:
                if Region.objects.filter(name=region_name, parent__id=parent_region).exists():
                    payload=build_response(
                        success=False,
                        code=status.HTTP_406_NOT_ACCEPTABLE,
                        message="Already exists."
                    )
                    return Response(payload, status=status.HTTP_406_NOT_ACCEPTABLE)  
                try:
                    parent_region_object = Region.objects.get(id=parent_region)
                except Region.DoesNotExist:
                    payload=build_response(
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message=f"{parent_region} is not a valid parent, please select an existing parent region"
                    )
                    return Response(payload, status=status.HTTP_400_BAD_REQUEST)    
                new_region_instance = Region(name=region_name, parent=parent_region_object)
                new_region_instance.save()
                payload = build_response(
                    success=True,
                    code=status.HTTP_201_CREATED,
                    message=f"{region_name} has been created as a child to {parent_region_object.name}"
                )
                return Response(payload, status=status.HTTP_201_CREATED)
            else:
                if Region.objects.filter(name=region_name, parent=None).exists():
                    payload = build_response(
                        success=False,
                        code=status.HTTP_406_NOT_ACCEPTABLE,
                        message="Region already exists"
                    )
                    return Response(payload, status=status.HTTP_406_NOT_ACCEPTABLE)          
                parent_region_instance = Region(name=region_name)
                parent_region_instance.save()
                payload = build_response(
                    success=True,
                    code=status.HTTP_201_CREATED,
                    message=f"{region_name} has been created as a root region"
                )
                return Response(payload, status=status.HTTP_201_CREATED)
        
        else:
            payload = build_response(
                success=False,
                code=status.HTTP_400_BAD_REQUEST,
                message="name is required"
            )
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)


    #Update Endpoint
    @extend_schema(
        summary = "Region Update",
        description = "Update regions.",
        tags = ["Region"],
        auth=[{"cookieAuth": []}],
        parameters = [
            OpenApiParameter(
                name="name",
                required=True,
                type=OpenApiTypes.STR,
                description="Region name",
            ),
            OpenApiParameter(
                name="parent",
                required=False,
                type=OpenApiTypes.INT,
                description="Parent Region ID",
            ),
        ],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = True,
                description = "Update region success",
                examples = [
                    swagger_response(
                        name="Region updated successfully",
                        success=True,
                        code=status.HTTP_200_OK,
                        message="Region updated successfully."
                    ),
                ] 
            ),
            status.HTTP_400_BAD_REQUEST :  OpenApiResponse(
                response = True,
                description = "Update region error",
                examples = [
                    swagger_response(
                        name="Invalid parent region",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "1 is not a valid parent, please select an existing parent region"
                    ),
                    swagger_response(
                        name="Name or parent is required",
                        success=False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "name or parent is required"
                    ),
                ]                
            ),
            status.HTTP_404_NOT_FOUND : OpenApiResponse(
                response = True,
                description = "Region not found",
                examples = [
                    swagger_response(
                        name = "Region not found",
                        success = False,
                        code = status.HTTP_404_NOT_FOUND,
                        message = "Region not found."
                    ),
                ]  
            ),
            status.HTTP_406_NOT_ACCEPTABLE :  OpenApiResponse(
                response = True,
                description = "Update region error",
                examples = [
                    swagger_response(
                        name = "Already exists with name and parent",
                        success = False,
                        code = status.HTTP_406_NOT_ACCEPTABLE,
                        message = "Already exists"
                    ),
                    swagger_response(
                        name = "Already exists with name",
                        success = False,
                        code = status.HTTP_406_NOT_ACCEPTABLE,
                        message = "Already exists"
                    ),
                    swagger_response(
                        name = "Already exists with parent",
                        success = False,
                        code = status.HTTP_406_NOT_ACCEPTABLE,
                        message = "Already exists"
                    ),
                ]                
            ),
        }
    )
    def update(self, request, pk=None):
        region_name = request.data.get('name')
        parent_region = request.data.get('parent')

        if region_name or parent_region:
            if region_name and parent_region:
                if Region.objects.filter(name=region_name, parent__id=parent_region).exists():
                    payload = build_response(
                        success= False,
                        code=status.HTTP_406_NOT_ACCEPTABLE,
                        message="Already exists"
                    )
                    return Response(payload, status=status.HTTP_406_NOT_ACCEPTABLE)
            elif region_name:
                if Region.objects.filter(name=region_name).exists():
                    payload = build_response(
                        success= False,
                        code=status.HTTP_406_NOT_ACCEPTABLE,
                        message="Already exists"
                    )
                    return Response(payload, status=status.HTTP_406_NOT_ACCEPTABLE)
            elif parent_region:
                if Region.objects.filter(id=pk, parent__id=parent_region).exists():
                    payload = build_response(
                        success= False,
                        code=status.HTTP_406_NOT_ACCEPTABLE,
                        message="Already exists"
                    )
                    return Response(payload, status=status.HTTP_406_NOT_ACCEPTABLE)
            try:
                region = Region.objects.get(id=pk)
                if region_name:
                    region.name = region_name
                if parent_region:
                    try:
                        parent_region_instance = Region.objects.get(id=parent_region)
                        region.parent = parent_region_instance
                    except Region.DoesNotExist:
                        payload=build_response(
                            success=False,
                            code=status.HTTP_400_BAD_REQUEST,
                            message=f'{parent_region} is not a valid parent, please select an existing parent region'
                        )
                        return Response(payload, status=status.HTTP_400_BAD_REQUEST) 
                region.save()
                payload = build_response(
                    success=True,
                    code=status.HTTP_200_OK,
                    message="Region updated successfully"
                )
                return Response(payload, status=status.HTTP_200_OK)
            except Region.DoesNotExist:
                payload = build_response(
                    success=False,
                    code=status.HTTP_404_NOT_FOUND,
                    message="Region not found",
                )
                return Response(payload, status=status.HTTP_404_NOT_FOUND)
        else:
            payload = build_response(
                success=False,
                code=status.HTTP_400_BAD_REQUEST,
                message="name or parent is required"
            )
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)


    #Partial Update
    @extend_schema(
        summary = "Region Partial Update",
        description = "Partial Update regions.",
        tags = ["Region"],
        responses = {
            status.HTTP_405_METHOD_NOT_ALLOWED : OpenApiResponse(
                response = True,
                description = "Not available",
                examples = [
                    swagger_response(
                        name = "Not available",
                        success = False,
                        code = status.HTTP_405_METHOD_NOT_ALLOWED,
                        message = "partial update endpoint is not available. Please use the update endpoint"
                    ),
                ]  
            )
        }
    )    
    def partial_update(self, request, pk=None):
        payload = build_response(
            success=False,
            code=status.HTTP_405_METHOD_NOT_ALLOWED,
            message="This endpoint is not available. Please use the update endpoint"
        )
        return Response(payload, status=status.HTTP_405_METHOD_NOT_ALLOWED)


    #Delete
    @extend_schema(
        summary = "Region Delete",
        description = "Delete regions.",
        tags = ["Region"],
        auth=[{"cookieAuth": []}],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = True,
                description = "Region deleted successfully",
                examples = [
                    swagger_response(
                        name = "Region deleted successfully",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Region deleted successfully."
                    ),
                ]  
            ),
            status.HTTP_404_NOT_FOUND : OpenApiResponse(
                response = True,
                description = "Region not found",
                examples = [
                    swagger_response(
                        name = "Region not found",
                        success = False,
                        code = status.HTTP_404_NOT_FOUND,
                        message = "Region not found."
                    ),
                ]  
            )
        }
    )  
    def destroy(self, request, pk=None):
        try:
            region_instance = Region.objects.get(id=pk)
            region_instance.delete()
            payload=build_response(
                success=True,
                code=status.HTTP_200_OK,
                message="Region deleted successfully"
            )
            return Response(payload, status=status.HTTP_200_OK)
        except Region.DoesNotExist:
            payload=build_response(
                success=False,
                code=status.HTTP_404_NOT_FOUND,
                message="Region not found"
            )
            return Response(payload, status=status.HTTP_404_NOT_FOUND)