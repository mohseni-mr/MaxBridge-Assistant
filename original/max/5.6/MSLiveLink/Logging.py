import socket, sys, os, json

parent_dir = os.path.abspath(os.path.dirname(__file__))
package = os.path.join(parent_dir, 'RequestLibrary')
sys.path.insert(0,package)
from RequestLibrary import requests

# For Handling all kinds of Logging
class Logger:
    def __init__(self, renderer, version, guid, assetID, bridge_event):
        try:
            self.renderer_version = ''
            self.renderer =renderer
            self.renderer = str(self.renderer).replace("_", ".")
            self.version = version
            self.guid = guid
            self.assetID = assetID
            self.bridge_event =  bridge_event
            self.renderer_version = self.SetupRendererVersion()
            self.BridgeLog()
            self.Metabase()
        except:
            pass
    # For Sending the data to Bridge Log File
    
    def GetData(self):
        from MS_API import MSLIVELINK_VERSION

        data = {
            'event': 'MAX_ASSET_IMPORT',
            'data':{
                'bridge_event': self.bridge_event,
                'asset_ID': self.assetID,
                'guid': self.guid,
                'plugin_version' : MSLIVELINK_VERSION,
                'app_version' : self.version,
                'renderer_version': self.renderer_version,
                'renderer' : self.renderer,
            }
        }
        
        return data

    def SetupRendererVersion(self):
        renderer_version = ''
        try:
            import pymxs
            if self.renderer == "Arnold":
                if self.version == 2020:
                    renderer_version = '2.4.43'
                elif self.version == 2021:
                    renderer_version = str(pymxs.runtime.execute("MAXtoAInterface.ArnoldVersion()")).split('[')[0]
                    renderer_version = renderer_version.split('Arnold')[1]
                elif self.version >= 2022:
                    renderer_version = str(pymxs.runtime.execute("MAXtoAOps.ArnoldVersion()")).split('[')[0]
                    renderer_version = renderer_version.split('Arnold')[1]
                else:
                    renderer_version = 'NA'
            elif self.renderer == "CoronaRenderer":
                renderer_version = str(pymxs.runtime.execute("CoronaRenderer.getVersionString()")).split(',')[0]
                self.renderer = "Corona"
            elif self.renderer.startswith("Redshift"):
                renderer_version = str(pymxs.runtime.execute("rsVersion()"))
                renderer_version = renderer_version[2:-1]
                renderer_version = renderer_version.replace(', ', '.')
                self.renderer = "Redshift"
            elif self.renderer.startswith("FStormRender"):
                renderer_version = self.renderer.split('FStormRender.')[1]
                self.renderer = "FStorm"
            elif self.renderer.startswith("V.Ray"):
                renderer_version = self.renderer.split('V.Ray.')[1]
                self.renderer = "V-Ray"
            elif self.renderer.startswith("OctaneRender"):
                self.renderer = str(self.renderer).replace("...", " - ")
                renderer_version = self.renderer.split('OctaneRender.')[1]
                self.renderer = "Octane"
        except Exception as e:
            print("Renderer Version Couldn't Be Fetched ", e)
        
        return renderer_version

    def BridgeLog(self):
        try:
            port = self.GetActivePort()
            url = "http://localhost:" + port + "/log/"
            response = requests.post(url,json= self.GetData())
           #print("Bridge Logging Response : ", response)
        except:
            pass
            #print("Bridge Logging Exception")
    
    # Open Local Connection to get Port from Bridge
    def GetActivePort(self):
        HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
        PORT = 28852        # Port to listen on (non-privileged ports are > 1023)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        activeport = sock.recv(32)
        sock.close()
        
        return activeport.decode("utf-8") 
    
    # # For Sending the data to Metabase
    def Metabase(self):
        port = self.GetActivePort()
        url = "http://localhost:" + port + "/analytics/"
        try:
            requests.post(url, data= json.dumps(self.GetData()))
        except:
            pass
            #print("Metabase Exception")
