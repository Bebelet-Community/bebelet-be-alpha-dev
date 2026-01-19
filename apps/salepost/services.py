from django.db import transaction

from apps.salepost.models import SalePost, SalePostAttribute
from apps.category.models import Attribute


@transaction.atomic
def create_salepost_atomic(
    *,
    post_id,
    seller,
    category,
    region,
    post_title, 
    description, 
    product_price, 
    latitude, 
    longitude, 
    min_usage, 
    max_usage, 
    category_attributes
):
    salepost = SalePost.objects.create(
        post_id=postid, 
        seller=seller, 
        category=category, 
        region=region, 
        post_title=post_title, 
        description=description, 
        product_price=product_price, 
        latitude=latitude, 
        longitude=longitude, 
        min_usage=min_usage, 
        max_usage=max_usage
    )

    attr_ids = [a.id for a in category_attributes]
    attrs = Attribute.objects.in_bulk(attr_ids)

    to_create=[]
    for category_att in category_attributes:
        att_value = attributes_payload.get(category_att.unique_name)
        if att_value in (None, ""):
            continue

        att_obj = attrs.get(category_att.id)
        if not att_obj:
            raise Attribute.DoesNotExist(f"Attribute not found: {category_att.id}")

        to_create.append(
            SalePostAttribute(
                salepost=salepost,
                attribute=att_obj,
                value=att_value,
            )
        )

    if to_create:
        SalePostAttribute.objects.bulk_create(to_create)

    return salepost

