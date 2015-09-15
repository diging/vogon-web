from rest_framework import serializers
from django.contrib.auth.models import User
from models import *
from concepts.models import Concept, Type

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'id')


class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository


class RelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relation


class AppellationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appellation
        # fields = ('createdBy', 'interpretation', 'occursIn', 'stringRep', 'tokenIds', 'id')


class TemporalBoundsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemporalBounds


class TextSerializer(serializers.ModelSerializer):
    class Meta:
        model = Text
        fields = ('id', 'uri', 'tokenizedContent', 'title', 'created', 'added',
                  'addedBy', 'source', 'annotators', 'annotationCount')

class TextCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextCollection


class ConceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concept
        fields = ('id', 'url', 'uri', 'label', 'authority', 'typed', 'description')


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = ('id', 'url', 'uri', 'label', 'authority', 'typed', 'description')
