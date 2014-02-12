
import event

def output_sitemap(event_name, site):
    pout.v(site)


event.listen('output_stop', output_sitemap)

