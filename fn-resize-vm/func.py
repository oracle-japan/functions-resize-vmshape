import io
import json
import oci

from fdk import response


def increase_compute_shapes(instance_id, add_ocpu, add_memory):
    signer = oci.auth.signers.get_resource_principals_signer()
    compute_client = oci.core.ComputeClient(config={}, signer=signer)

    current_ocpus = compute_client.get_instance(
        instance_id).data.shape_config.ocpus
    current_memory = compute_client.get_instance(
        instance_id).data.shape_config.memory_in_gbs

    print("INFO: current ocpu and memory for Instance {0}: ocpu:{1} memory:{2}".format(
        instance_id, current_ocpus, current_memory), flush=True)

    try:
        shape_config = oci.core.models.UpdateInstanceShapeConfigDetails(
            ocpus=current_ocpus + add_ocpu, memory_in_gbs=current_memory + add_memory)
        update_instance_details = oci.core.models.UpdateInstanceDetails(
            shape_config=shape_config)
        resp = compute_client.update_instance(
            instance_id=instance_id, update_instance_details=update_instance_details)
        print(resp.data, resp.status, flush=True)
    except Exception as ex:
        print('ERROR: cannot update instance {}'.format(instance_id), flush=True)
        raise

    return "The shape of Instance {} is updated, the instance is rebooting...".format(instance_id)


def handler(ctx, data: io.BytesIO = None):
    alarm_msg = {}
    message_id = func_response = ""
    cfg = ctx.Config()
    print(str(ctx.Config()))

    try:
        headers = ctx.Headers()
        message_id = headers["x-oci-ns-messageid"]
        ocpu = cfg["OCPU"]
        memory = cfg["MEMORY"]
        if ocpu is None:
            ocpu = 1.0
        if memory is None:
            memory = 1.0
    except Exception as ex:
        print('ERROR: Missing Items', ex, flush=True)
        raise
    print('INFO: headers', headers, flush=True)
    print("INFO: Message ID = ", message_id, flush=True)
    print('INFO: add_ocpu', ocpu, flush=True)
    print('INFO: add_memory', memory, flush=True)

    try:
        alarm_msg = json.loads(data.getvalue())
        print("INFO: Alarm message: ")
        print(alarm_msg, flush=True)
    except (Exception, ValueError) as ex:
        print(str(ex), flush=True)

    if alarm_msg["type"] == "OK_TO_FIRING":
        if alarm_msg["alarmMetaData"][0]["dimensions"]:
            alarm_metric_dimension = alarm_msg["alarmMetaData"][0]["dimensions"][0]
            print("INFO: Instance to resize: ",
                  alarm_metric_dimension["resourceId"], flush=True)
            func_response = increase_compute_shapes(
                alarm_metric_dimension["resourceId"], float(ocpu), float(memory))
            print("INFO: ", func_response, flush=True)
        else:
            print('ERROR: There is no metric dimension in this alarm message', flush=True)
            func_response = "There is no metric dimension in this alarm message"
    else:
        print('INFO: Nothing to do, alarm is not FIRING', flush=True)
        func_response = "Nothing to do, alarm is not FIRING"

    return response.Response(
        ctx,
        response_data=func_response,
        headers={"Content-Type": "application/json"}
    )
