from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from core.permissions import HasPerm
from core.responses import build_response, swagger_response

from apps.salepost.models import SalePost
from apps.salepost.serializers import SalePostListSerializer

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse



class SalePostPagination(PageNumberPagination):
    page_size = 20  # Default page size
    page_size_query_param = 'limit'  # Allow ?limit=40
    max_page_size = 100


class SalePostViewSet(ModelViewSet):
    queryset = SalePost.objects.filter(post_status='published')
    serializer_class = SalePostListSerializer
    pagination_class = SalePostPagination

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), HasPerm("salepost.add_salepost")]
        elif self.action == "update":
            return [IsAuthenticated(), HasPerm("salepost.change_salepost")]
        elif self.action == "destroy":
            return [IsAuthenticated(), HasPerm("salepost.delete_salepost")]
        else:
            return []


    #List Endpoint
    @extend_schema(
        summary = "Salepost List",
        description = "Retrive salepost list.",
        tags = ["Salepost"],
        parameters = [
            OpenApiParameter(
                name="user_latitude",
                required=False,
                type=OpenApiTypes.FLOAT,
                description="User latitude for distance filtering/sorting.",
            ),
            OpenApiParameter(
                name="user_longitude",
                required=False,
                type=OpenApiTypes.FLOAT,
                description="User longitude for distance filtering/sorting.",
            ),
            OpenApiParameter(
                name="user_region_id",
                required=False,
                type=OpenApiTypes.INT,
                description="User region id to derive latitude/longitude.",
            ),
            OpenApiParameter(
                name="max_distance",
                required=False,
                type=OpenApiTypes.FLOAT,
                description="Max distance in km (used with distance filtering).",
            ),
            OpenApiParameter(
                name="sort_by",
                required=False,
                type=OpenApiTypes.STR,
                enum=["published_at", "distance", "price"],
                description="Sort field."
            ),
            OpenApiParameter(
                name="order",
                required=False,
                type=OpenApiTypes.STR,
                enum=["asc", "desc"],
                description="Sort order."
            ),
            OpenApiParameter(
                name="category_ids",
                required=False,
                type=OpenApiTypes.STR,
                description="Comma separated category ids. Example: 1,2,3",
            ),
            OpenApiParameter(
                name="region_ids",
                required=False,
                type=OpenApiTypes.STR,
                description="Comma separated region ids. Example: 1,2,3",
            ),
            OpenApiParameter(
                name="price_min",
                required=False,
                type=OpenApiTypes.FLOAT,
                description="Minimum price.",
            ),
            OpenApiParameter(
                name="price_max",
                required=False,
                type=OpenApiTypes.FLOAT,
                description="Maximum price.",
            ),
            OpenApiParameter(
                name="published_last_days",
                required=False,
                type=OpenApiTypes.INT,
                description="Show posts published in last N days.",
            ),
            OpenApiParameter(
                name="keyword",
                required=False,
                type=OpenApiTypes.STR,
                description="Search in title or description.",
            ),
        ],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = True,
                description = "Saleposts retrieved.",
                examples = [
                    swagger_response(
                        name = "Saleposts retrieved successfully",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Saleposts retrieved successfully.",
                        data = {
                            "count": 1,
                            "next": None,
                            "previous": None,
                            "results": [
                                {
                                    "post_id": 0,
                                    "post_status": "published",
                                    "seller": "admin",
                                    "category": "Category1",
                                    "region": "Region3",
                                    "post_title": "Salepost1",
                                    "description": "This is a salepost 1",
                                    "posted_at": "2026-01-18T17:56:53Z",
                                    "viewed": 0,
                                    "latitude": None,
                                    "longitude": None,
                                    "product_price": "1.00",
                                    "attributes": None,
                                    "images": None
                                }
                            ]
                        }
                    )
                ]
            ), 
            status.HTTP_400_BAD_REQUEST : OpenApiResponse(
                response = True,
                description = "Saleposts retrieved error",
                examples = [
                    swagger_response(
                        name = "Saleposts retrieved error",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "user_latitude & user_longitude or user_region_id is required for distance filtering or sorting.",               
                    ),
                    swagger_response(
                        name = "Saleposts retrieved error",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Provide either user_region_id or user_latitude/user_longitude, not both.",               
                    ),
                    swagger_response(
                        name = "Saleposts retrieved error",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "user_latitude and user_longitude must be used together.",               
                    ),
                    swagger_response(
                        name = "Saleposts retrieved error",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Invalid latitude or longitude.",               
                    ),
                    swagger_response(
                        name = "Saleposts retrieved error",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Latitude or longitude out of range.",               
                    ),
                    swagger_response(
                        name = "Saleposts retrieved error",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Invalid filtering value: Test",               
                    ),
                    swagger_response(
                        name = "Saleposts retrieved error",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Invalid max_distance value",               
                    ),
                    swagger_response(
                        name = "Saleposts retrieved error",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Invalid sort_by value. Must be 'price', 'published_at', or 'distance'.",               
                    ),
                ]
            ),
            status.HTTP_404_NOT_FOUND : OpenApiResponse(
                response = True,
                description = "Salepost not found.",
                examples = [
                    swagger_response(
                        name = "Salepost not found",
                        success = False,
                        code = status.HTTP_404_NOT_FOUND,
                        message = "Salepost not found.",
                    ),
                ]
            ), 
        }
    )
    def list(self, request):
        query_params = request.query_params

        # Fetch parameters
        user_lat = query_params.get("user_latitude")
        user_lon = query_params.get("user_longitude")
        user_region_id = query_params.get("user_region_id")
        max_distance = query_params.get("max_distance")

        if max_distance and max_distance > 50:  # max value for max_distance parameter
            max_distance = 50

        sort_by = query_params.get("sort_by", "published_at")  # default sort
        order = query_params.get("order", "asc")  # default order

        # Distance filtering requested, require location input
        if (max_distance or sort_by == "distance"):
            if not ((user_lat and user_lon) or user_region_id):
                payload = build_response(
                    success=False,
                    code=status.HTTP_400_BAD_REQUEST,
                    message="user_latitude & user_longitude or user_region_id is required for distance filtering or sorting."
                )
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)
            if user_lat and user_lon and user_region_id:
                payload = build_response(
                    success=False,
                    code=status.HTTP_400_BAD_REQUEST,
                    message="Provide either user_region_id or user_latitude/user_longitude, not both."
                )
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)
            if (user_lat and not user_lon) or (not user_lat and user_lon):
                payload = build_response(
                    success=False,
                    code=status.HTTP_400_BAD_REQUEST,
                    message="user_latitude and user_longitude must be used together."
                )
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)

            if user_lat and user_lon:
                try:
                    user_lat = round(float(user_lat), 6)
                    user_lon = round(float(user_lon), 6)
                except ValueError:
                    payload = build_response(
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="Invalid latitude or longitude."
                    )
                    return Response(payload, status=status.HTTP_400_BAD_REQUEST)
            else:
                try:
                    region = Region.objects.get(id=user_region_id)
                    user_lat = region.latitude
                    user_lon = region.longitude
                except Region.DoesNotExist:
                    payload = build_response(
                        success=False,
                        code=status.HTTP_404_NOT_FOUND,
                        message="Region not found."
                    )
                    return Response(payload, status=status.HTTP_404_NOT_FOUND)

            if not (-90 <= user_lat <= 90 and -180 <= user_lon <= 180):
                payload = build_response(
                    success=True,
                    code=status.HTTP_400_BAD_REQUEST,
                    message="Latitude or longitude out of range."
                )
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        # Begin post filtering
        posts = SalePost.objects.filter(post_status='published').select_related('region')
        try:
            category_ids = query_params.get("category_ids")
            if category_ids:
                category_id_list = [int(cid.strip()) for cid in category_ids.split(",") if cid.strip().isdigit()]
                all_category_ids = get_all_descendant_category_ids(category_id_list)
                posts = posts.filter(category_id__in=all_category_ids)

            region_ids = query_params.get("region_ids")
            if region_ids:
                region_id_list = [int(rid.strip()) for rid in region_ids.split(",") if rid.strip().isdigit()]
                all_region_ids = get_all_descendant_region_ids(region_id_list)
                posts = posts.filter(region_id__in=all_region_ids)

            price_min = query_params.get("price_min")
            if price_min:
                posts = posts.filter(product_price__gte=int(price_min))

            price_max = query_params.get("price_max")
            if price_max:
                posts = posts.filter(product_price__lte=int(price_max))

            published_last_days = query_params.get("published_last_days")
            if published_last_days:
                days = int(published_last_days)
                cutoff = timezone.now() - timezone.timedelta(days=days)
                posts = posts.filter(posted_at__gte=cutoff)

        except ValueError as e:
            payload = build_response(
                success = False,
                code = status.HTTP_400_BAD_REQUEST,
                message=f"Invalid filtering value: {str(e)}"
            )
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        keyword = query_params.get("keyword")
        if keyword: 
            posts = posts.filter(Q(post_title__icontains=keyword) | Q(description__icontains=keyword))

        # Calculate distances only if required
        if max_distance or sort_by == "distance":
            latitudes = [p.effective_latitude for p in posts]
            longitudes = [p.effective_longitude for p in posts]
            distances = haversine_vectorized(user_lat, user_lon, latitudes, longitudes)
            for post, dist in zip(posts, distances):
                post._distance_km = dist

            if max_distance:
                try:
                    max_distance = float(max_distance)
                    posts = [p for p in posts if p._distance_km <= max_distance]
                except ValueError:
                    payload = build_response(
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="Invalid max_distance value"
                    )
                    return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        # Sorting
        reverse = (order == "desc")
        if sort_by == "price":
            posts_sorted = sorted(posts, key=lambda p: p.product_price or 0, reverse=reverse)
        elif sort_by == "published_at":
            posts_sorted = sorted(posts, key=lambda p: p.posted_at or timezone.datetime.min, reverse=reverse)
        elif sort_by == "distance":
            posts_sorted = sorted(posts, key=lambda p: getattr(p, "_distance_km", float("inf")), reverse=reverse)
        else:
            payload = build_response(
                success=False,
                code=status.HTTP_400_BAD_REQUEST,
                message="Invalid sort_by value. Must be 'price', 'published_at', or 'distance'."
            )
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        # Pagination
        page = self.paginate_queryset(posts_sorted)
        if page is not None:
            serialized = SalePostListSerializer(page, many=True)
            for obj in serialized.data:
                post = next(p for p in page if p.post_id == obj["post_id"])
                if hasattr(post, "_distance_km"):
                    obj["distance_km"] = (
                        "Less than 1 km" if post._distance_km < 1 else f"{post._distance_km:.2f} km"
                    )
            return self.get_paginated_response(serialized.data)

        serialized = SalePostListSerializer(posts_sorted, many=True)
        return Response(serialized.data)


    #Retrive Endpoint
    @extend_schema(
        summary="Salepost Retrieve",
        description="Retrieve a single salepost by post_id.",
        tags = ["Salepost"],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = SalePostListSerializer,
                description = "Saleposts retrieved.",
                examples = [
                    swagger_response(
                        name = "Saleposts retrieved successfully",
                        success = True,
                        code = status.HTTP_200_OK,
                        message = "Saleposts retrieved successfully.",
                        data = {
                            "post_id": 0,
                            "post_status": "published",
                            "seller": "bebelet_user",
                            "category": "Category1",
                            "region": "Region3",
                            "post_title": "Salepost1",
                            "description": "This is a salepost 1",
                            "posted_at": "2026-01-18T17:56:53Z",
                            "viewed": 1,
                            "latitude": None,
                            "longitude": None,
                            "product_price": "1.00",
                            "attributes": None,
                            "images": None
                        }
                    )
                ]
            ), 
            status.HTTP_404_NOT_FOUND : OpenApiResponse(
                response = True,
                description="Salepost not found.",
                examples = [
                    swagger_response(
                        name = "Salepost not found",
                        success = False,
                        code = status.HTTP_404_NOT_FOUND,
                        message = "Salepost not found.",
                    )
                ]
            ), 
        }
    )
    def retrieve(self, request, pk=None):
        try:
            salepost_instance = SalePost.objects.get(post_id=pk)
            serializer = SalePostListSerializer(salepost_instance)
            salepost_instance.viewed += 1
            salepost_instance.save()
            payload = build_response(
                success = True,
                code = status.HTTP_200_OK,
                message = "Salepost retrived successfully",
                data = serializer.data
            )
            return Response(payload, status=status.HTTP_200_OK)
        except SalePost.DoesNotExist:
            payload = build_response(
                success=False,
                code=status.HTTP_404_NOT_FOUND,
                message="Salepost not found"
            )
            return Response(payload, status=status.HTTP_404_NOT_FOUND)

    #Create Endpoint
    @extend_schema(
        summary = "Salepost Create",
        description = "Create salepost",
        tags = ["Salepost"],
        parameters = [
            OpenApiParameter(
                name="category",
                required=True,
                type=OpenApiTypes.INT,
                description="Category id for new salepost",
            ),
            OpenApiParameter(
                name="region",
                required=True,
                type=OpenApiTypes.INT,
                description="region id for new salepost",
            ),
            OpenApiParameter(
                name="post_title",
                required=True,
                type=OpenApiTypes.STR,
                description="post_title for new salepost",
            ),
            OpenApiParameter(
                name="description",
                required=True,
                type=OpenApiTypes.STR,
                description="description for new salepost",
            ),
            OpenApiParameter(
                name="product_price",
                required=True,
                type=OpenApiTypes.FLOAT,
                description="product_price for new salepost",
            ),
            OpenApiParameter(
                name="latitude",
                required=True,
                type=OpenApiTypes.FLOAT,
                description="latitude for new salepost",
            ),
            OpenApiParameter(
                name="longitude",
                required=True,
                type=OpenApiTypes.FLOAT,
                description="longitude for new salepost",
            ),
            OpenApiParameter(
                name="min_usage",
                required=False,
                type=OpenApiTypes.INT,
                description="min_usage id for new salepost",
            ),
            OpenApiParameter(
                name="max_usage",
                required=False,
                type=OpenApiTypes.INT,
                description="max_usage id for new salepost",
            ),
        ],
        responses = {
            status.HTTP_201_CREATED : OpenApiResponse(
                response=True,
                description="Create Salepost",
                examples=[
                    swagger_response(
                        name="Salepost has been created",
                        success=True,
                        code=status.HTTP_201_CREATED,
                        message="Salepost has been created",
                        data = {
                            "postId": "000000",
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST : OpenApiResponse(
                response=True,
                description="Create Salepost Error",
                examples = [
                    swagger_response(
                        name = "Min usage range id is not valid",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Min usage range id is not valid."
                    ),
                    swagger_response(
                        name = "Max usage range id is not valid",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Max usage range id is not valid."
                    ),
                    swagger_response(
                        name = "Min usage range must be less than or equal to max usage range",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Min usage range must be less than or equal to max usage range."
                    ),
                    swagger_response(
                        name = "Category id is not valid",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Category id is not valid."
                    ),
                    swagger_response(
                        name = "Region id is not valid",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Region id is not valid."
                    ),
                    swagger_response(
                        name = "Product price is required and must be a number",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Product price is required and must be a number."
                    ),
                    swagger_response(
                        name = "Product price cannot be negative",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Product price cannot be negative."
                    ),
                    swagger_response(
                        name = "Invalid latitude or longitude",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Invalid latitude or longitude."
                    ),
                    swagger_response(
                        name = "Invalid latitude or longitude",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Latitude or longitude out of range."
                    ),
                    swagger_response(
                        name = "Attribute1 is required",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Attribute1 is required."
                    ),
                    swagger_response(
                        name = "Attribute1 must be a number",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Attribute1 must be a number."
                    ),
                    swagger_response(
                        name = "Attribute2 must be a string",
                        success = False,
                        code = status.HTTP_400_BAD_REQUEST,
                        message = "Attribute2 must be a string."
                    )
                ]
            )
        }
    )
    def create(self, request):
        postid = generate_unique_post_id()
        seller = request.user
        category = request.data.get('category')
        region = request.data.get('region')
        post_title = request.data.get('post_title')
        description = request.data.get('description')
        product_price = request.data.get('product_price')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        min_usage = request.data.get('min_usage')
        max_usage = request.data.get('max_usage')

        if request.data.get('min_usage'):
            try:
                min_usage = UsageRange.objects.get(id=min_usage)
            except UsageRange.DoesNotExist:
                payload = build_response(
                    success = True,
                    code = status.HTTP_400_BAD_REQUEST,
                    message = "Min usage range id is not valid.",
                )
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                min_usage = UsageRange.objects.get(unique_id=-1)
            except UsageRange.DoesNotExist:
                payload = build_response(
                    success=False,
                    code=status.HTTP_400_BAD_REQUEST,
                    message="Min usage range id is not valid."
                )
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)
            
        if request.data.get('max_usage'):
            try:
                max_usage = UsageRange.objects.get(id=max_usage)
            except UsageRange.DoesNotExist:
                payload=build_response(
                    success=False,
                    code=status.HTTP_400_BAD_REQUEST,
                    message="Max usage range id is not valid.",
                )
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                max_usage = UsageRange.objects.get(unique_id=-1)
            except UsageRange.DoesNotExist:
                payload = build_response(
                    success=False,
                    code=status.HTTP_400_BAD_REQUEST,
                    message="Max usage range id is not valid."
                )
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)
            
        if min_usage.unique_id > max_usage.unique_id:
            payload = build_response(
                success=False,
                code=status.HTTP_400_BAD_REQUEST,
                message="Min usage range must be less than or equal to max usage range."
            )
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        try:
            category_instance = Category.objects.get(id=category)
        except Category.DoesNotExist:
            payload = build_response(
                success=False,
                code=status.HTTP_400_BAD_REQUEST,
                message="Category id is not valid."
            )
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            region_instance = Region.objects.get(id=region)
        except Region.DoesNotExist:
            payload = build_response(
                success=False,
                code=status.HTTP_400_BAD_REQUEST,
                message="Region id is not valid."
            )
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)
        
        if product_price is None or not isinstance(product_price, (int, float)):
            payload = build_response(
                success=False,
                code=status.HTTP_400_BAD_REQUEST,
                message="Product price is required and must be a number."
            )
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)
        
        if product_price < 0:
            payload = build_response(
                success=False,
                code=status.HTTP_400_BAD_REQUEST,
                message="Product price cannot be negative."
            )
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)
        

        try:
            latitude = round(float(latitude), 6)
            longitude = round(float(longitude), 6)
        except ValueError:
            payload = build_response(
                success=False,
                code=status.HTTP_400_BAD_REQUEST,
                message="Invalid latitude or longitude."
            )
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)


        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            payload = build_response(
                success=False,
                code=status.HTTP_400_BAD_REQUEST,
                message="Latitude or longitude out of range."
            )
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)


        category_attributes = Attribute.objects.filter(categories=category_instance)
 
        for categoryAtt in category_attributes:
            att_obj = Attribute.objects.get(id=categoryAtt.id)
            att_value = request.data.get(categoryAtt.unique_name)
            
            if not att_value and categoryAtt.is_required:
                payload = build_response(
                    success=False,
                    code=status.HTTP_400_BAD_REQUEST,
                    message=f"{categoryAtt.unique_name} is required."
                )
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)
            
            if att_value:
                if att_obj.data_type == 'number' or  att_obj.data_type == 'choice':
                    if not isinstance(att_value, (int, float)):
                        payload = build_response(
                            success=False,
                            code=status.HTTP_400_BAD_REQUEST,
                            message=f"{categoryAtt.unique_name} must be a number."
                        )
                        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

                else:
                    if not isinstance(att_value, str):
                        payload = build_response(
                            success=False,
                            code=status.HTTP_400_BAD_REQUEST,
                            message=f"{categoryAtt.unique_name} must be a string."
                        )
                        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

                """
                if not ((att_obj.data_type == 'number' or att_obj.data_type == 'choice') and isinstance(att_value, (int, float))):
                    return Response({'error': f"{categoryAtt.unique_name} must be a number"}, status=status.HTTP_400_BAD_REQUEST)
            
                elif not (att_obj.data_type == 'text' and isinstance(att_value, str)):
                    return Response({'error': f"{categoryAtt.unique_name} must be a string"}, status=status.HTTP_400_BAD_REQUEST)
                """
        

        attributes_payload = dict(request.data)

        salepost_instance = create_salepost_atomic(
            post_id=postid,
            seller=seller,
            category=category_instance,
            region=region_instance,
            post_title=post_title,
            description=description,
            product_price=product_price,
            latitude=latitude,
            longitude=longitude,
            min_usage=min_usage,
            max_usage=max_usage,
            category_attributes=category_attributes,
            attributes_payload=attributes_payload,
        )

        payload = build_response(
            success=True,
            code=status.HTTP_201_CREATED,
            message="Salepost has been created.",
            data={"postId": salepost_instance.post_id},
        )

        return Response(payload, status=status.HTTP_201_CREATED)

    
    #Update endpoint
    @extend_schema(
        summary="Salepost Updated",
        description="Update Salepost",
        tags = ["Salepost"],
        parameters = [
            OpenApiParameter(
                name="post_title",
                required=False,
                type=OpenApiTypes.STR,
                description="post title for the salepost"
            ),
            OpenApiParameter(
                name="description",
                required=False,
                type=OpenApiTypes.STR,
                description="description for the salepost"
            ),
            OpenApiParameter(
                name="product_price",
                required=False,
                type=OpenApiTypes.FLOAT,
                description="product price for the salepost"
            ),
        ],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response=True,
                description="Salepost update",
                examples = [
                    swagger_response(
                        name="Salepost has been updated",
                        success=False,
                        code=status.HTTP_200_OK,
                        message="Salepost has been updated."
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST : OpenApiResponse(
                response=True,
                description = "Salepost update error",
                examples = [
                    swagger_response(
                        name="Product price is not valid",
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="Product price is not valid."
                    ),
                    swagger_response(
                        name="Attribute1 is required",
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="Attribute1 is required."
                    ),
                    swagger_response(
                        name="Attribute1 is required",
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="Attribute1 must be a number"
                    ),
                    swagger_response(
                        name="Attribute1 is required",
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="Attribute2 must be a string"
                    )
                ]
            ),
            status.HTTP_401_UNAUTHORIZED : OpenApiResponse(
                response=True,
                description = "Salepost access error",
                examples = [
                    swagger_response(
                        name="You have no access to edit",
                        success=False,
                        code=status.HTTP_401_UNAUTHORIZED,
                        message="You have no access to edit."
                    )
                ]
            )
        }
    )
    def update(self, request, pk=None):
        post_title = request.data.get('post_title')
        description = request.data.get('description')
        product_price = request.data.get('product_price')

        if product_price < 0:
            payload = build_response(
                status=False,
                code=status.HTTP_400_BAD_REQUEST,
                message="Product price is not valid."
            )
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        try:
            salepost_obj = SalePost.objects.get(id=pk)
            if not salepost_obj.seller == request.user:
                payload = build_response(
                    status=False,
                    code=status.HTTP_401_UNAUTHORIZED,
                    message="You have no access to edit"
                )
                return Response(payload, status=status.HTTP_401_UNAUTHORIZED)
        except SalePost.DoesNotExist:
            payload = build_response(
                status=False,
                code=status.HTTP_404_NOT_FOUND,
                message="Salepost not found"
            )
            return Response(payload, status=status.HTTP_404_NOT_FOUND)

        if post_title:
            salepost_obj.post_title = post_title
        if description:
            salepost_obj.description = description
        if product_price:
            salepost_obj.product_price = product_price

        category_attributes = Attribute.objects.filter(category=salepost_obj.category.id)
        for categoryAtt in category_attributes:
            att_obj = Attribute.objects.get(id=categoryAtt.id)
            att_value = request.data.get(categoryAtt.unique_name)
            if not att_value and categoryAtt.is_required:
                payload = build_response(
                    success=False,
                    code=status.HTTP_400_BAD_REQUEST,
                    message=f'{categoryAtt.unique_name} is required'
                )
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)
            
            if not ((att_obj.data_type == 'number' or att_obj.data_type == 'choice') and isinstance(att_value, (int, float))):
                payload = build_response(
                    success=False,
                    code=status.HTTP_400_BAD_REQUEST,
                    message=f"{categoryAtt.unique_name} must be a number."
                )
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)
            if not (att_obj.data_type == 'text' and isinstance(att_value, str)):
                payload = build_response(
                    success=False,
                    code=status.HTTP_400_BAD_REQUEST,
                    message=f"{categoryAtt.unique_name} must be a string"
                )
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        for categoryAtt in category_attributes:
            att_obj = Attribute.objects.get(id=categoryAtt.attribute.id)
            att_value = request.data.get(categoryAtt.unique_name)
            if att_value:
                try:
                    salePostAtt = SalePostAttribute.objects.get(salepost=salepost_obj, attribute=att_obj)
                    salePostAtt.value = att_value
                    salePostAtt.save()

                except SalePostAttribute.DoesNotExist:
                    salePostAtt = SalePostAttribute(salepost=salepost_obj, attribute=att_obj, value=att_value)
                    salePostAtt.save()

        payload = build_response(
            success=True,
            code=status.HTTP_200_OK,
            message="Salepost has been updated"
        )
        return Response(payload, status=status.HTTP_200_OK)


    @extend_schema(
        summary = "Salepost Partial Update",
        description = "Not available",
        tags = ["Salepost"],
        responses = {
            status.HTTP_405_METHOD_NOT_ALLOWED : OpenApiResponse(
                response=True,
                description="Not available",
                examples = [
                    swagger_response(
                        name="Not available",
                        success=False,
                        code=status.HTTP_405_METHOD_NOT_ALLOWED,
                        message="Partial update endpoint is not available. Please use the update endpoint."
                    )
                ]
            )
        }
    )
    def partial_update(self, request, pk=None):
        payload = build_response(
            success=False,
            code=status.HTTP_405_METHOD_NOT_ALLOWED,
            message="Partial update endpoint is not available. Please use the update endpoint"
        )
        return Response(payload, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    @extend_schema(
        summary = "Salepost Delete",
        description = "Delete salepost",
        tags = ["Salepost"],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response=True,
                description = "Salepost delete.",
                examples = [
                    swagger_response(
                        name="Salepost deleted successfully",
                        success=True,
                        code=status.HTTP_200_OK,
                        message="Salepost deleted successfully."
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND : OpenApiResponse(
                response=True,
                description = "Salepost delete.",
                examples = [
                    swagger_response(
                        name="Salepost not found",
                        success=False,
                        code=status.HTTP_404_NOT_FOUND,
                        message="Salepost not found."
                    )
                ]
            )
        }
    )
    def destroy(self, request, pk=None):
        try:
            salepost_obj = SalePost.objects.get(post_id=pk)
            salepost_obj.delete()
            payload = build_response(
                success=True,
                code=status.HTTP_200_OK,
                message="Salepost deleted successfully"
            )
            return Response(payload, status=status.HTTP_200_OK)
        except SalePost.DoesNotExist:
            payload = build_response(
                success=True,
                code=status.HTTP_404_NOT_FOUND,
                message="Salepost not found"
            )
            return Response(payload, status=status.HTTP_404_NOT_FOUND)


class SalePostHomeView(APIView):
    permission_classes = []


    @extend_schema(
        summary="Salepost list",
        description="Retrieve salepost",
        tags = ["Salepost"],
        parameters = [
            OpenApiParameter(
                name="min_usage",
                required=False,
                type=OpenApiTypes.INT,
                description="Filter by min_usage.",
            ),
            OpenApiParameter(
                name="max_usage",
                required=False,
                type=OpenApiTypes.INT,
                description="Filter by max_usage.",
            ),
            OpenApiParameter(
                name="gender",
                required=False,
                type=OpenApiTypes.STR,
                description="Filter by gender.",
            )
        ],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response = True,
                description = "Salepost retrieved.",
                examples = [
                    swagger_response(
                        name="Salepost retrived successfully",
                        success=True,
                        code=status.HTTP_200_OK,
                        message="Salepost retrived successfully."
                    ),
                ]
            ),
            status.HTTP_400_BAD_REQUEST : OpenApiResponse(
                response = True,
                description = "Salepost retrieved error.",
                examples = [
                    swagger_response(
                        name="min_usage and max_usage must be integers",
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="min_usage and max_usage must be integers."
                    ),
                    swagger_response(
                        name="min_usage must be an integer",
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="min_usage must be an integer."
                    ),
                    swagger_response(
                        name="max_usage must be an integer",
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="max_usage must be an integer."
                    ),
                ]
            )
        }

    )
    def get(self, request):
        min_usage = request.data.get('min_usage')
        max_usage = request.data.get('max_usage')
        gender = request.data.get('gender')

        if gender:
            gender_posts = SalePostAttribute.objects.filter(attribute__unique_name='gender', value=gender)
            if min_usage and max_usage:
                if isinstance(min_usage, int) and isinstance(max_usage, int):
                    latest_posts = SalePost.objects.filter(post_status='published', salepostattribute__in=gender_posts, min_usage_range__gte=min_usage, max_usage_range__lte=max_usage).order_by('-posted_at')[:16]
                else:
                    payload = build_response(
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="min_usage and max_usage must be integers."
                    )
                    Response(payload, status=status.HTTP_400_BAD_REQUEST)
            elif min_usage and not max_usage:
                if isinstance(min_usage, int):
                    latest_posts = SalePost.objects.filter(post_status='published', salepostattribute__in=gender_posts, min_usage_range__gte=min_usage).order_by('-posted_at')[:16]
                else:
                    payload = build_response(
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="min_usage must be an integer."
                    )
                    return Response(payload, status=status.HTTP_400_BAD_REQUEST)
            elif not min_usage and max_usage:
                if isinstance(max_usage, int):
                    latest_posts = SalePost.objects.filter(post_status='published', salepostattribute__in=gender_posts, max_usage_range__lte=max_usage).order_by('-posted_at')[:16]
                else:
                    payload = build_response(
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="max_usage must be an integer."
                    )
                    return Response(payload, status=status.HTTP_400_BAD_REQUEST)
            else:
                latest_posts = SalePost.objects.filter(post_status='published', salepostattribute__in=gender_posts).order_by('-posted_at')[:16]
        
        else:
            # All posts without any gender filter
            if min_usage and max_usage:
                if isinstance(min_usage, int) and isinstance(max_usage, int):
                    latest_posts = SalePost.objects.filter(post_status='published', min_usage_range__gte=min_usage, max_usage_range__lte=max_usage).order_by('-posted_at')[:16]
                else:
                    payload = build_response(
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="min_usage and max_usage must be integers."
                    )
                    return Response(payload, status=status.HTTP_400_BAD_REQUEST)
            elif min_usage and not max_usage:
                if isinstance(min_usage, int):
                    latest_posts = SalePost.objects.filter(post_status='published', min_usage_range__gte=min_usage).order_by('-posted_at')[:16]
                else:
                    payload = build_response(
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="min_usage must be an integer."
                    )
                    return Response(payload, status=status.HTTP_400_BAD_REQUEST)
            elif not min_usage and max_usage:
                if isinstance(max_usage, int):
                    latest_posts = SalePost.objects.filter(post_status='published', max_usage_range__lte=max_usage).order_by('-posted_at')[:16]
                else:
                    payload = build_response(
                        success=False,
                        code=status.HTTP_400_BAD_REQUEST,
                        message="max_usage must be an integer."
                    )
                    return Response(payload, status=status.HTTP_400_BAD_REQUEST)
            else:
                latest_posts = SalePost.objects.filter(post_status='published').order_by('-posted_at')[:16]
                serializer = SalePostListSerializer(latest_posts, many=True)
                payload = build_response(
                    success=True,
                    code=status.HTTP_200_OK,
                    message="Salepost retrived successfully",
                    data = serializer.data
                )
                return Response(payload, status=status.HTTP_200_OK)

                

class SalePostSimilarView(APIView):
    permission_classes = []

    @extend_schema(
        summary="Similar Salepost List",
        description="Get Similar Saleposts",
        tags=["Salepost"],
        responses = {
            status.HTTP_200_OK : OpenApiResponse(
                response=True,
                description="Similar Salepost",
                examples = [
                    swagger_response(
                        name="Salepost retrived successfully",
                        success=True,
                        code=status.HTTP_200_OK,
                        message="Salepost retrived successfully."
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND : OpenApiResponse(
                response=True,
                description="Similar Salepost Error",
                examples = [
                    swagger_response(
                        name="SalePost not found, cannot provide related posts",
                        success=False,
                        code=status.HTTP_404_NOT_FOUND,
                        message="SalePost not found, cannot provide related posts."
                    )
                ]
            )
        }
    )
    def get(self, request, public_id=None):
        MAX_RESPONSE_LENGTH = 5
        response_list = []
        # lets first grab the post with the provided id 
        try:
            sale_post_instance = SalePost.objects.get(post_id=pk)
        except SalePost.DoesNotExist:
            payload = build_response(
                success=False,
                code=status.HTTP_404_NOT_FOUND,
                message="SalePost not found, cannot provide related posts"
            )
            return Response(payload, status=status.HTTP_404_NOT_FOUND)
        

        # our post has this category instance
        category_instance = sale_post_instance.category  

        # group A, same category posts
        # lets grab all the posts with the same category
        list_of_posts_with_same_category = SalePost.objects.filter(category=category_instance).exclude(id=sale_post_instance.id).order_by('-posted_at')[:MAX_RESPONSE_LENGTH]
        
        if (len(list_of_posts_with_same_category) == MAX_RESPONSE_LENGTH):
            serializer = SalePostListSerializer(list_of_posts_with_same_category, many=True)
            payload = build_response(
                success=True,
                code=status.HTTP_200_OK,
                message="Salepost retrived successfully",
                data = serializer.data
            )
            return Response(payload, status=status.HTTP_200_OK)

        
        for i in range(len(list_of_posts_with_same_category)):
               response_list.append(list_of_posts_with_same_category[i])
        
        
        # group B, sibling category posts
        # Get all sibling categories
        list_of_sibling_categories = Category.objects.filter(parent_category=category_instance.parent_category)
        list_of_posts_with_sibling_category = SalePost.objects.filter(category__in=list_of_sibling_categories).exclude(id=sale_post_instance.id).order_by('-posted_at')[:MAX_RESPONSE_LENGTH]

        for i in range(len(list_of_posts_with_sibling_category)):
            response_list.append(list_of_posts_with_sibling_category[i])
            #remove duplicates from list
            response_list = list(dict.fromkeys(response_list))
            if len(response_list) >= MAX_RESPONSE_LENGTH:
                serializer = SalePostListSerializer(response_list, many=True)
                payload = build_response(
                    success=True,
                    code=status.HTTP_200_OK,
                    message="Salepost retrived successfully",
                    data=serializer.data,
                )
                return Response(payload, status=status.HTTP_200_OK)
                
        
        #group C, cousin category posts
        # parent category instance of our post 
        try:
            parent_category_instance = Category.objects.get(name=category_instance.parent_category)
        except Category.DoesNotExist:
            parent_category_instance = None

        if parent_category_instance != None:
            list_of_uncle_categories = Category.objects.filter(parent_category=parent_category_instance.parent_category)
            list_of_cousin_categories = Category.objects.filter(parent_category__in=list_of_uncle_categories)
            list_of_posts_with_cousin_category = SalePost.objects.filter(category__in=list_of_cousin_categories).exclude(id=sale_post_instance.id).order_by('-posted_at')[:MAX_RESPONSE_LENGTH]

            for i in range(len(list_of_posts_with_cousin_category)):
                response_list.append(list_of_posts_with_cousin_category[i])
                #remove duplicates from list
                response_list = list(dict.fromkeys(response_list))
                if len(response_list) >= MAX_RESPONSE_LENGTH:
                    break

        serializer = SalePostListSerializer(response_list, many=True)
        payload = build_response(
            success=True,
            code=status.HTTP_200_OK,
            message="Salepost retrived successfully",
            data=serializer.data
        )
        return Response(payload, status=status.HTTP_200_OK)
