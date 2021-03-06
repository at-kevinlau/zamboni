import json
import logging

from django.db import transaction
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.response import Response

from mkt.api.authentication import RestOAuthAuthentication
from mkt.api.authorization import GroupPermission
from mkt.api.base import CORSMixin

from .forms import MonolithForm
from .models import MonolithRecord


logger = logging.getLogger('z.monolith')


class MonolithSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonolithRecord

    def transform_value(self, obj, value):
        return json.loads(value)


class MonolithViewSet(CORSMixin, mixins.DestroyModelMixin,
                      mixins.ListModelMixin, mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    cors_allowed_methods = ('get', 'delete')
    permission_classes = [GroupPermission('Monolith', 'API')]
    authentication_classes = [RestOAuthAuthentication]
    serializer_class = MonolithSerializer

    def get_queryset(self):
        form = MonolithForm(self.request.QUERY_PARAMS)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        key = form.cleaned_data['key']
        start = form.cleaned_data['start']
        end = form.cleaned_data['end']

        qs = MonolithRecord.objects.all()
        if key:
            qs = qs.filter(key=key)
        if start is not None:
            qs = qs.filter(recorded__gte=start)
        if end is not None:
            qs = qs.filter(recorded__lt=end)
        return qs

    @transaction.commit_on_success
    def delete(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        logger.info('Deleting %d monolith resources' % qs.count())
        qs.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
