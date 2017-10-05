package vdiskstorage

import (
	"encoding/json"
	"net/http"
	"sync"

	"fmt"
	"github.com/gorilla/mux"
	ays "github.com/zero-os/0-orchestrator/api/ays-client"
	"github.com/zero-os/0-orchestrator/api/tools"
)

// ListImages is the handler for GET /vdiskstorage/{vdiskstorageid}/images
// List all vdisk images installed in this VdiskStroage
func (api *VdiskstorageAPI) ListImages(w http.ResponseWriter, r *http.Request) {
	aysClient, err := tools.GetAysConnection(api)
	if err != nil {
		tools.WriteError(w, http.StatusUnauthorized, err, "")
		return
	}

	vdiskstorageid := mux.Vars(r)["vdiskstorageid"]
	query := map[string]interface{}{
		"parent": fmt.Sprintf("vdiskstorage!%s", vdiskstorageid),
		"fields": "diskBlockSize,size",
	}

	services, res, err := aysClient.Ays.ListServicesByRole("vdisk_image", api.AysRepo, nil, query)
	if !tools.HandleAYSResponse(err, res, w, "listing vdisk_images") {
		return
	}

	var (
		images = make([]Image, len(services))
		errs   = make([]error, len(services))
		wg     = sync.WaitGroup{}
	)
	wg.Add(len(services))
	for i, service := range services {
		go func(i int, service ays.ServiceData) {
			defer wg.Done()

			var image Image
			if err := json.Unmarshal(service.Data, &image); err != nil {
				errs[i] = err
				return
			}
			image.Name = service.Name
			images[i] = image

		}(i, service)
	}

	wg.Wait()

	// TODO: concatenate all  errors into one
	for _, err := range errs {
		if err != nil {
			tools.WriteError(w, http.StatusInternalServerError, err, "Error getting list of images")
			return
		}
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(&images)
}
