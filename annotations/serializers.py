from rest_framework import serializers
from annotations.models import VogonUser
from .models import *
from repository.models import Repository as RepositoryModel
from concepts.models import Concept, Type


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = VogonUser
        fields = ('username', 'email', 'id', 'affiliation', 'location',
                  'full_name', 'link')


class RemoteCollectionSerializer(serializers.Serializer):
    source = serializers.IntegerField()
    id_or_uri = serializers.CharField(max_length=255)
    name = serializers.CharField(max_length=255)


class RemoteResourceSerializer(serializers.Serializer):
    source = serializers.IntegerField()
    id_or_uri = serializers.CharField(max_length=255)
    title = serializers.CharField(max_length=255)


class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RepositoryModel
        fields = '__all__'


class RelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relation
        fields = '__all__'


class DocumentPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentPosition
        fields = '__all__'


class DateAppellationSerializer(serializers.ModelSerializer):
    position = DocumentPositionSerializer(required=False)

    class Meta:
        model = DateAppellation
        fields = ('created', 'createdBy', 'id', 'occursIn', 'position', 'year',
                  'month', 'day', 'project', 'stringRep', 'dateRepresentation')


class TextSerializer(serializers.ModelSerializer):
    class Meta:
        model = Text
        fields = ('id', 'uri', 'title', 'created', 'added', 'addedBy',
                  'source', 'annotators', 'annotation_count', 'children')

    def create(self, validated_data):
        repository = Repository.objects.get(pk=validated_data['source'])
        # TODO: Make retrieval/tokenization/other processing asynchronous.
        tokenizedContent = tokenize(
            retrieve(repository, validated_data['uri']))

        text = Text(
            uri=validated_data['uri'],
            title=validated_data['title'],
            source=repository,
            addedBy=self.context['request'].user,
            tokenizedContent=tokenizedContent)
        text.save()
        return HttpResponse(text.id)


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = ('id', 'url', 'uri', 'label', 'authority', 'typed',
                  'description')


class ConceptSerializer(serializers.ModelSerializer):
    typed = TypeSerializer(required=False)

    class Meta:
        model = Concept
        fields = ('id', 'url', 'uri', 'label', 'authority', 'typed',
                  'description', 'pos', 'resolved', 'typed_label',
                  'concept_state', 'appellation_set')


class AppellationSerializer(serializers.ModelSerializer):
    position = DocumentPositionSerializer(required=False)
    tokenIds = serializers.CharField(required=False)
    stringRep = serializers.CharField(required=False)
    occursIn = TextSerializer(required=False)
    interpretation = ConceptSerializer(required=False)
    createdBy = UserSerializer()

    class Meta:
        model = Appellation
        fields = ('asPredicate', 'created', 'createdBy', 'endPos', 'id',
                  'interpretation', 'interpretation_type', 'occursIn',
                  'startPos', 'stringRep', 'tokenIds', 'interpretation_label',
                  'interpretation_type_label', 'position', 'project')

class AppellationPOSTSerializer(serializers.ModelSerializer):
    position = DocumentPositionSerializer(required=False)
    tokenIds = serializers.CharField(required=False)
    stringRep = serializers.CharField(required=False)

    class Meta:
        model = Appellation
        fields = ('asPredicate', 'created', 'createdBy', 'endPos', 'id',
                  'interpretation', 'interpretation_type', 'occursIn',
                  'startPos', 'stringRep', 'tokenIds', 'interpretation_label',
                  'interpretation_type_label', 'position', 'project')


class RelationSetSerializer(serializers.ModelSerializer):
    appellations = AppellationSerializer(many=True)
    date_appellations = DateAppellationSerializer(many=True)
    concepts = ConceptSerializer(many=True)
    createdBy = UserSerializer()

    class Meta:
        model = RelationSet
        fields = ('id', 'label', 'created', 'template', 'createdBy',
                  'occursIn', 'appellations', 'concepts', 'project',
                  'representation', 'date_appellations', 'submitted',
                  'submittedOn', 'pending')  #


class TemporalBoundsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemporalBounds
        fields = '__all__'


class TextCollectionSerializer(serializers.ModelSerializer):
    class VogonUserSerializer(serializers.ModelSerializer):
        class Meta:
            model = VogonUser
            fields = ['id', 'username']
    
    ownedBy = VogonUserSerializer()
    num_texts = serializers.IntegerField()
    num_relations = serializers.IntegerField()
    
    class Meta:
        model = TextCollection
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextCollection
        fields = '__all__'


class ProjectTextSerializer(TextCollectionSerializer):
    class TextSerializer(serializers.ModelSerializer):
        class Meta:
            model = Text
            fields = ['id', 'title', 'added', 'repository_id', 'repository_source_id']
    texts = TextSerializer(many=True, read_only=True)

class TemplatePartSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelationTemplate
        fields = ('id', 'name', 'description')


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelationTemplate
        fields = ('id', 'name', 'description', 'template_parts')
        depth = 1
