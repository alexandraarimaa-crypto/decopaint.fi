from rest_framework import serializers
from .models import Product, Variant

class VariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variant
        fields = ['item_code', 'item_description', 'barcode', 'price', 'color', 'size', 'image', 'thumbnail']

class ProductSerializer(serializers.ModelSerializer):
    variants = VariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category', 'image', 'available', 'variants']
