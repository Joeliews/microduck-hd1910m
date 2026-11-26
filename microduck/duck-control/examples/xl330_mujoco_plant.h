#ifndef XL330_MUJOCO_PLANT_H
#define XL330_MUJOCO_PLANT_H

/* Opaque plant. The Rust control loop calls these; mj_step lives in plant_step_n. */

typedef struct Plant Plant;

Plant* plant_open(const char* xml, char* err, int err_n);
void plant_close(Plant* plant);
int plant_reset_stand(Plant* plant);
void plant_set_physics_dt(Plant* plant, double dt);
double plant_physics_dt(const Plant* plant);
void plant_zero_sensor_noise(Plant* plant);
int plant_nu(const Plant* plant);
int plant_nq(const Plant* plant);
int plant_actuator_joint_names(const Plant* plant, char* buf, int n);
void plant_home_ctrl(const Plant* plant, double* out);
void plant_copy_q(const Plant* plant, double* out);
void plant_copy_qpos(const Plant* plant, double* out);
void plant_set_ctrl(Plant* plant, const double* ctrl);
void plant_step_n(Plant* plant, int n);
void plant_kick_vx(Plant* plant, double vx);
void plant_sense(const Plant* plant, double gyro[3], double quat[4], double qd[14], double* trunk_z);
int plant_warning_count(const Plant* plant);

#endif
