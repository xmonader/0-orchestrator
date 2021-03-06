package vdisk

import (
	"encoding/json"
	"fmt"

	"net/http"

	"github.com/gorilla/mux"
	"github.com/zero-os/0-orchestrator/api/tools"
)

// ResizeVdisk is the handler for POST /vdisks/{vdiskid}/resize
// Resize Vdisk
func (api *VdisksAPI) ResizeVdisk(w http.ResponseWriter, r *http.Request) {
	aysClient, err := tools.GetAysConnection(api)
	if err != nil {
		tools.WriteError(w, http.StatusUnauthorized, err, "")
		return
	}
	var reqBody VdiskResize

	vdiskID := mux.Vars(r)["vdiskid"]

	// decode request
	if err := json.NewDecoder(r.Body).Decode(&reqBody); err != nil {
		tools.WriteError(w, http.StatusBadRequest, err, "Error decoding request body")
		return
	}

	// validate request
	if err := reqBody.Validate(); err != nil {
		tools.WriteError(w, http.StatusBadRequest, err, "")
		return
	}

	srv, resp, err := aysClient.Ays.GetServiceByName(vdiskID, "vdisk", api.AysRepo, nil, nil)
	if !tools.HandleAYSResponse(err, resp, w, fmt.Sprintf("getting info about vdisk %s", vdiskID)) {
		return
	}

	var vDisk Vdisk
	if err := json.Unmarshal(srv.Data, &vDisk); err != nil {
		tools.WriteError(w, http.StatusInternalServerError, err, "Error unmarshaling ays response")
		return
	}

	if vDisk.Size > reqBody.NewSize {
		err := fmt.Errorf("newSize: %v is smaller than current size %v.", reqBody.NewSize, vDisk.Size)
		tools.WriteError(w, http.StatusBadRequest, err, "")
		return
	}

	// Create resize blueprint
	bp := struct {
		Size int `yaml:"size" json:"size"`
	}{
		Size: reqBody.NewSize,
	}

	decl := fmt.Sprintf("vdisk__%v", vdiskID)

	obj := make(map[string]interface{})
	obj[decl] = bp

	// And execute

	_, err = aysClient.ExecuteBlueprint(api.AysRepo, "vdisk", vdiskID, "resize", obj)

	errmsg := fmt.Sprintf("error executing blueprint for vdisk %s resize", vdiskID)
	if !tools.HandleExecuteBlueprintResponse(err, w, errmsg) {
		return
	}

	w.WriteHeader(http.StatusNoContent)
}
