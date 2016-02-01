var fsu = function() {
	var token = null;

	var handlers = {};
	handlers.error = alert;
	handlers.notImpl = function() {
		alert("Not implemented: " + toString(arguments));
	}
	handlers.addAccount = handlers.notImpl;
	handlers.updateAccount = handlers.notImpl;
	handlers.deleteAccount = handlers.notImpl;

	function getChanges() {
		var xhr = new XMLHttpRequest();
		xhr.onreadystatechange = function() {processChanges(xhr);};
		var fd = new FormData();
		fd.set("token", token);
		xhr.open("POST", "/get", true);
		xhr.send(fd);
	}

	function processChanges(xhr) {
		var resp;
		if(xhr.readyState == 4) {
			if(xhr.status != 200) {
				if(xhr.statusText.length > 0) {
					handlers.error("Bad status: " + xhr.statusText);
				} else {
					handlers.error("Bad status (connection refused)");
				}
				return;
			}
			if(typeof(xhr.response) == "string") {
				resp = eval("(" + xhr.responseText + ")");
			}
			if(resp.token != null) {
				token = resp.token;
			}
			if(resp.error != null) {
				handlers.error("Error " + resp.error.code + ": " + resp.error.reason);
				return;
			}
			if(resp.changes != null) {
				for(var idx = 0; idx < resp.changes.length; idx++) {
					var change = resp.changes[idx];
					switch(change.type) {
						case "add":
							handlers.addAccount(change.acct);
							break;
						case "update":
							handlers.updateAccount(change.acct);
							break;
						case "delete":
							handlers.deleteAccount(change.acct);
							break;
						default:
							handlers.error("Unknown change type: " + change.type);
							break;
					}
				}
			}
		}
	}

	return {
		"handlers": handlers,
		"getChanges": getChanges,
	};
}();
