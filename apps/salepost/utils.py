from apps.category.models import Category
from apps.region.models import Region

def get_all_descendant_region_ids(region_ids):
    all_ids = set()
    regions_to_process = list(Region.objects.filter(id__in=region_ids))

    while regions_to_process:
        region = regions_to_process.pop()
        all_ids.add(region.id)
        children = list(region.subregions.all())
        regions_to_process.extend(children)

    return list(all_ids)



def get_all_descendant_category_ids(category_ids):
    all_ids = set()
    categories_to_process = list(Category.objects.filter(id__in=category_ids))

    while categories_to_process:
        category = categories_to_process.pop()
        all_ids.add(category.id)
        children = list(category.subcategories.all())
        categories_to_process.extend(children)

    return list(all_ids)