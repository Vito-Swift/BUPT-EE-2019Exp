from bokeh.models.callbacks import CustomJS
from exp_packages.loadingOverlay import loadingOverlay_js

query_loading_spinning = CustomJS(args=dict(), code=loadingOverlay_js + """
var spinHandle = loadingOverlay.activate();
setTimeout(function() {
   loadingOverlay.cancel(spinHandle);
},2000);
""")
plot_loading_spinning = CustomJS(args=dict(), code=loadingOverlay_js + """
var spinHandle = loadingOverlay.activate();
setTimeout(function() {
   loadingOverlay.cancel(spinHandle);
},200);
""")
