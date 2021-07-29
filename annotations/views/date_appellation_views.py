from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response

from annotations.models import DateAppellation, DocumentPosition
from annotations.serializers import DateAppellationSerializer, DocumentPositionSerializer

class DateAppellationViewSet(viewsets.ModelViewSet):
    queryset = DateAppellation.objects.all()
    serializer_class = DateAppellationSerializer

    def create(self, request):
        data = request.data.copy()
        position = data.pop('position', None)
        if 'month' in data and data['month'] is None:
            data.pop('month')
        if 'day' in data and data['day'] is None:
            data.pop('day')
            
        data['createdBy'] = request.user.id
        
        serializer = DateAppellationSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        text_id = serializer.data.get('occursIn')
        if position:
            if not isinstance(position, DocumentPosition):
                position_serializer = DocumentPositionSerializer(data=position)
                position_serializer.is_valid(raise_exception=True)
                position = position_serializer.save()

            instance.position = position
            instance.save()

        instance.refresh_from_db()
        reserializer = DateAppellationSerializer(instance, context={'request': request})
        headers = self.get_success_headers(serializer.data)
        return Response(
            reserializer.data, 
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def partial_update(self, request, *args, **kwargs):
        instance_object = self.get_object()
        data = request.data.copy()
        position = data.pop('position', None)
        if 'month' in data and data['month'] is None:
            data['month'] = 0
        if 'day' in data and data['day'] is None:
            data['day'] = 0
            
        serializer = DateAppellationSerializer(instance_object, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        if position:
            if not isinstance(position, DocumentPosition):
                position_serializer = DocumentPositionSerializer(instance_object.position, data=position, partial=True)
                position_serializer.is_valid(raise_exception=True)
                position = position_serializer.save()

            instance.position = position
            instance.save()

        instance.refresh_from_db()
        reserializer = DateAppellationSerializer(instance, context={'request': request})
        headers = self.get_success_headers(serializer.data)
        return Response(
            reserializer.data, 
            status=status.HTTP_200_OK,
            headers=headers
        )
        