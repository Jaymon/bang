# -*- coding: utf-8 -*-
"""
Google Analytics


You can find your GA_TRACKING_ID by:

    * log into your GA account
    * Click Admin.
    * Select an account from the menu in the ACCOUNT column.
    * Select a property from the menu in the PROPERTY column.
    * Under PROPERTY, click Tracking Info > Tracking Code.
      Your Google Analytics ID is displayed at the top of the page.

    https://support.google.com/analytics/answer/1008080#trackingID
"""
import logging

from ..compat import *
from ..event import event


logger = logging.getLogger(__name__)


@event("output.template")
def template_output_ga(event):
    config = event.config

    ga_tracking_id = config.get("ga_tracking_id", None)
    if not ga_tracking_id:
        logger.error("Google Analytics plugin missing config.ga_tracking_id")
        return

    if config.is_context("amp"):
        # https://developers.google.com/analytics/devguides/collection/amp-analytics/#basic_setup_to_measure_page_views
        s = """<script async custom-element="amp-analytics" src="https://cdn.ampproject.org/v0/amp-analytics-0.1.js"></script>
        <amp-analytics type="gtag" data-credentials="include">
        <script type="application/json">
        {{
        "vars" : {{
            "gtag_id": "<{GA_TRACKING_ID}>",
            "config" : {{
            "<{GA_TRACKING_ID}>": {{ "groups": "default" }}
            }}
        }}
        }}
        </script>
        </amp-analytics>"""

    else:
        s = """<!-- Global site tag (gtag.js) - Google Analytics -->
            <script async src="https://www.googletagmanager.com/gtag/js?id={GA_TRACKING_ID}"></script>
            <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('js', new Date());

            gtag('config', '{GA_TRACKING_ID}');
            </script>"""

    event.html = event.html.inject_into_body(
        s.format(GA_TRACKING_ID=ga_tracking_id)
    )

