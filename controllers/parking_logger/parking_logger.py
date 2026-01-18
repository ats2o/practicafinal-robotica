from controller import Robot

def main() -> None:
    robot = Robot()
    timestep = int(robot.getBasicTimeStep())

    front_sensor = robot.getDevice("ds_front")
    right_sensor = robot.getDevice("ds_right")

    front_sensor.enable(timestep)
    right_sensor.enable(timestep)

    while robot.step(timestep) != -1:
        front_value = front_sensor.getValue()
        right_value = right_sensor.getValue()
        print(f"ds_front={front_value:.3f} ds_right={right_value:.3f}")


if __name__ == "__main__":
    main()
