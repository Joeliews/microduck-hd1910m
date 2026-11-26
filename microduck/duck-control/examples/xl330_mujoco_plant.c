#include "xl330_mujoco_plant.h"

#include <mujoco/mujoco.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NPOLICY 14

struct Plant {
    mjModel* model;
    mjData* data;
    int qadr[NPOLICY];
    int dadr[NPOLICY];
    int quat_adr;
    int gyro_adr;
    int trunk;
};

static void fail(char* err, int err_n, const char* msg) {
    if (err && err_n > 0) {
        snprintf(err, (size_t)err_n, "%s", msg);
    }
}

Plant* plant_open(const char* xml, char* err, int err_n) {
    char load_err[1024] = {0};
    mjModel* model = mj_loadXML(xml, NULL, load_err, (int)sizeof(load_err));
    if (!model) {
        fail(err, err_n, load_err[0] ? load_err : "mj_loadXML failed");
        return NULL;
    }
    mjData* data = mj_makeData(model);
    if (!data) {
        mj_deleteModel(model);
        fail(err, err_n, "mj_makeData failed");
        return NULL;
    }
    if (model->nu != NPOLICY) {
        mj_deleteData(data);
        mj_deleteModel(model);
        fail(err, err_n, "model nu is not 14");
        return NULL;
    }
    Plant* plant = calloc(1, sizeof(*plant));
    if (!plant) {
        mj_deleteData(data);
        mj_deleteModel(model);
        fail(err, err_n, "out of memory");
        return NULL;
    }
    plant->model = model;
    plant->data = data;
    for (int i = 0; i < NPOLICY; i++) {
        if (model->actuator_trntype[i] != mjTRN_JOINT) {
            plant_close(plant);
            fail(err, err_n, "actuator transmission is not a joint");
            return NULL;
        }
        int joint = model->actuator_trnid[i * 2];
        plant->qadr[i] = model->jnt_qposadr[joint];
        plant->dadr[i] = model->jnt_dofadr[joint];
    }
    int quat = mj_name2id(model, mjOBJ_SENSOR, "orientation");
    int gyro = mj_name2id(model, mjOBJ_SENSOR, "imu_ang_vel");
    int trunk = mj_name2id(model, mjOBJ_BODY, "trunk_base");
    if (quat < 0 || gyro < 0 || trunk < 0) {
        plant_close(plant);
        fail(err, err_n, "missing orientation, imu_ang_vel, or trunk_base");
        return NULL;
    }
    plant->quat_adr = model->sensor_adr[quat];
    plant->gyro_adr = model->sensor_adr[gyro];
    plant->trunk = trunk;
    if (model->sensor_dim[quat] != 4 || model->sensor_dim[gyro] != 3) {
        plant_close(plant);
        fail(err, err_n, "unexpected IMU sensor width");
        return NULL;
    }
    return plant;
}

void plant_close(Plant* plant) {
    if (!plant) {
        return;
    }
    if (plant->data) {
        mj_deleteData(plant->data);
    }
    if (plant->model) {
        mj_deleteModel(plant->model);
    }
    free(plant);
}

int plant_reset_stand(Plant* plant) {
    int key = mj_name2id(plant->model, mjOBJ_KEY, "STAND");
    if (key < 0) {
        return -1;
    }
    mj_resetDataKeyframe(plant->model, plant->data, key);
    mj_forward(plant->model, plant->data);
    return 0;
}

void plant_set_physics_dt(Plant* plant, double dt) {
    plant->model->opt.timestep = dt;
}

double plant_physics_dt(const Plant* plant) {
    return plant->model->opt.timestep;
}

void plant_zero_sensor_noise(Plant* plant) {
    for (int i = 0; i < plant->model->nsensor; i++) {
        plant->model->sensor_noise[i] = 0;
    }
}

int plant_nu(const Plant* plant) { return plant->model->nu; }
int plant_nq(const Plant* plant) { return plant->model->nq; }

int plant_actuator_joint_names(const Plant* plant, char* buf, int n) {
    if (n <= 0) {
        return -1;
    }
    buf[0] = 0;
    int used = 0;
    for (int i = 0; i < NPOLICY; i++) {
        int joint = plant->model->actuator_trnid[i * 2];
        const char* name = mj_id2name(plant->model, mjOBJ_JOINT, joint);
        if (!name) {
            return -1;
        }
        int wrote = snprintf(buf + used, (size_t)(n - used), "%s%s", i ? "," : "", name);
        if (wrote < 0 || wrote >= n - used) {
            return -1;
        }
        used += wrote;
    }
    return 0;
}

void plant_home_ctrl(const Plant* plant, double* out) {
    for (int i = 0; i < NPOLICY; i++) {
        out[i] = plant->data->ctrl[i];
    }
}

void plant_copy_q(const Plant* plant, double* out) {
    for (int i = 0; i < NPOLICY; i++) {
        out[i] = plant->data->qpos[plant->qadr[i]];
    }
}

void plant_copy_qpos(const Plant* plant, double* out) {
    for (int i = 0; i < plant->model->nq; i++) {
        out[i] = plant->data->qpos[i];
    }
}

void plant_set_ctrl(Plant* plant, const double* ctrl) {
    for (int i = 0; i < NPOLICY; i++) {
        plant->data->ctrl[i] = ctrl[i];
    }
}

void plant_step_n(Plant* plant, int n) {
    for (int i = 0; i < n; i++) {
        mj_step(plant->model, plant->data);
    }
}

void plant_kick_vx(Plant* plant, double vx) {
    plant->data->qvel[0] += vx;
    mj_forward(plant->model, plant->data);
}

void plant_sense(const Plant* plant, double gyro[3], double quat[4], double qd[14], double* trunk_z) {
    const mjtNum* s = plant->data->sensordata;
    for (int i = 0; i < 4; i++) {
        quat[i] = s[plant->quat_adr + i];
    }
    for (int i = 0; i < 3; i++) {
        gyro[i] = s[plant->gyro_adr + i];
    }
    for (int i = 0; i < NPOLICY; i++) {
        qd[i] = plant->data->qvel[plant->dadr[i]];
    }
    *trunk_z = plant->data->xpos[plant->trunk * 3 + 2];
}

int plant_warning_count(const Plant* plant) {
    int n = 0;
    for (int i = 0; i < mjNWARNING; i++) {
        n += plant->data->warning[i].number;
    }
    return n;
}
