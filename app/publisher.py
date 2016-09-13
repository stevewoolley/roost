import paho.mqtt.publish as publish
from paho.mqtt.client import MQTTv311
import ssl


class Publisher:
    """A MQTT Publisher object"""

    def __init__(self, endpoint, root_ca, key, cert, port=8883):
        self.endpoint = endpoint
        self.root_ca = root_ca
        self.key = key
        self.cert = cert
        self.port = port

    def publish(self, topic, obj, qos=0, retain=False):
        msg = {'topic': topic, 'payload': obj, 'qos': qos, 'retain': retain}
        publish.multiple([msg],
                         hostname=self.endpoint,
                         port=self.port,
                         tls={'ca_certs': self.root_ca,
                              'certfile': self.cert,
                              'keyfile': self.key,
                              'tls_version': ssl.PROTOCOL_TLSv1
                              }
                         ,
                         protocol=MQTTv311)

    def publish_multiple(self, obj):
        publish.multiple(obj,
                         hostname=self.endpoint,
                         port=self.port,
                         tls={'ca_certs': self.root_ca,
                              'certfile': self.cert,
                              'keyfile': self.key,
                              'tls_version': ssl.PROTOCOL_TLSv1
                              }
                         ,
                         protocol=MQTTv311)
