from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response

from annotations.models import DateAppellation, DocumentPosition
from annotations.serializers import DateAppellationSerializer, DocumentPositionSerializer

class DateAppellationViewSet(viewsets.ModelViewSet):
    queryset = DateAppellation.objects.all()
    serializer_class = DateAppellationSerializer

    def create(self, request):
        data = request.data
        position = data.pop('position', None)
        return_data = "Something went wrong, unable to save the data"
        if 'month' in data and data['month'] is None:
            data['month'] = 0
        if 'day' in data and data['day'] is None:
            data['day'] = 0
            
        data['createdBy'] = request.user.id
        
        serializer = DateAppellationSerializer(data=data)
        if not serializer.is_valid():
            return Response(data=return_data, status=HTTP_400_BAD_REQUEST)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        text_id = serializer.data.get('occursIn')
        if position:
            if not isinstance(position, DocumentPosition):
                position_serializer = DocumentPositionSerializer(data=position)
                if not position_serializer.is_valid():
                    return Response(data=return_data, status=HTTP_400_BAD_REQUEST)
                instance.position = position_serializer.save()
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
        data = request.data
        position = data.pop('position', None)
        return_data = "Something went wrong, unable to save the data"
        if 'month' in data and data['month'] is None:
            data['month'] = 0
        if 'day' in data and data['day'] is None:
            data['day'] = 0
            
        serializer = DateAppellationSerializer(instance_object, data=data, partial=True)
        if not serializer.is_valid():
            return Response(data=return_data, status=HTTP_400_BAD_REQUEST)
            
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        if position:
            if not isinstance(position, DocumentPosition):
                position_serializer = DocumentPositionSerializer(instance_object.position, data=position, partial=True)
                position_serializer.is_valid(raise_exception=True)
                if not position_serializer.is_valid():
                    return Response(data=return_data, status=HTTP_400_BAD_REQUEST)
                instance.position = position_serializer.save()
                instance.save()

        instance.refresh_from_db()
        reserializer = DateAppellationSerializer(instance, context={'request': request})
        headers = self.get_success_headers(serializer.data)
        return Response(
            reserializer.data, 
            status=status.HTTP_200_OK,
            headers=headers
        )
        