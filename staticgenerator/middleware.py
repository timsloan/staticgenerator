import re
import urllib
from django.conf import settings
from staticgenerator import StaticGenerator


class StaticGeneratorMiddleware(object):
    """
    This requires settings.STATIC_GENERATOR_URLS tuple to match on URLs

    Example::

        STATIC_GENERATOR_URLS = (
            r'^/$',
            r'^/blog',
        )

    Sometimes people try stuff like this:

        ``index.html?page=../../../../../../../../../../proc/self``

        STATIC_GENERATOR_QUERYSTRINGS = (
            'page',
            'print',
        )

    """
    urls = tuple([re.compile(url) for url in settings.STATIC_GENERATOR_URLS])
    querystrings_allowed = tuple([q for q in settings.STATIC_GENERATOR_QUERYSTRINGS])
    excluded_urls = tuple([re.compile(url) for url in getattr(settings, 'STATIC_GENERATOR_EXCLUDE_URLS', [])])
    gen = StaticGenerator()

    def process_response(self, request, response):
        path = request.path_info

        if response.status_code == 200:
            query_string_dict = request.GET.copy()

            if getattr(settings, 'STATIC_GENERATOR_ANONYMOUS_ONLY', False) and not request.user.is_anonymous():
                return response

            final_querystring = dict()
            for key in query_string_dict.keys():
                if key in self.querystrings_allowed:
                    final_querystring[key] = query_string_dict[key]

            excluded = False
            for url in self.excluded_urls:
                if url.match(path):
                    excluded = True
                    break

            if not excluded:
                for url in self.urls:
                    if url.match(path):
                        self.gen.publish_from_path(path, urllib.urlencode(final_querystring, True), response.content)
                        break

        return response
