from django.db import models

class Region(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="subregions")
    latitude = models.CharField(max_length=12, blank=True, null=True)
    longitude = models.CharField(max_length=12, blank=True, null=True)

    class Meta:
        permissions = []

    def __str__(self):
        return self.name

