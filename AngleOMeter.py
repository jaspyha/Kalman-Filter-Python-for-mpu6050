#Connections
#MPU6050 - Raspberry pi
#VCC - 5V  (2 or 4 Board)
#GND - GND (6 - Board)
#SCL - SCL (5 - Board)
#SDA - SDA (3 - Board)


from Kalman import KalmanAngle
import smbus			#import SMBus module of I2C
import time
import math
import RPi.GPIO as GPIO

IMU1 = 11
IMU2 = 13
IMU3 = 15

GPIO.setmode(GPIO.BOARD)
GPIO.setup(IMU1, GPIO.OUT)
GPIO.setup(IMU2, GPIO.OUT)
GPIO.setup(IMU3, GPIO.OUT)

kalmanX = [KalmanAngle(),KalmanAngle(),KalmanAngle()]
kalmanY = [KalmanAngle(),KalmanAngle(),KalmanAngle()]

RestrictPitch = True	#Comment out to restrict roll to ±90deg instead - please read: http://www.freescale.com/files/sensors/doc/app_note/AN3461.pdf
radToDeg = 57.2957786
kalAngleX = [0,0,0]
kalAngleY = [0,0,0]
#some MPU6050 Registers and their Address
PWR_MGMT_1   = 0x6B
SMPLRT_DIV   = 0x19
CONFIG       = 0x1A
GYRO_CONFIG  = 0x1B
INT_ENABLE   = 0x38
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H  = 0x43
GYRO_YOUT_H  = 0x45
GYRO_ZOUT_H  = 0x47


#Read the gyro and acceleromater values from MPU6050
def MPU_Init():
	#write to sample rate register
	bus.write_byte_data(DeviceAddress, SMPLRT_DIV, 7)

	#Write to power management register
	bus.write_byte_data(DeviceAddress, PWR_MGMT_1, 1)

	#Write to Configuration register
	#Setting DLPF (last three bit of 0X1A to 6 i.e '110' It removes the noise due to vibration.) https://ulrichbuschbaum.wordpress.com/2015/01/18/using-the-mpu6050s-dlpf/
	bus.write_byte_data(DeviceAddress, CONFIG, int('0000110',2))

	#Write to Gyro configuration register
	bus.write_byte_data(DeviceAddress, GYRO_CONFIG, 24)

	#Write to interrupt enable register
	bus.write_byte_data(DeviceAddress, INT_ENABLE, 1)


def read_raw_data(addr):
	#Accelero and Gyro value are 16-bit
        high = bus.read_byte_data(DeviceAddress, addr)
        low = bus.read_byte_data(DeviceAddress, addr+1)

        #concatenate higher and lower value
        value = ((high << 8) | low)

        #to get signed value from mpu6050
        if(value > 32768):
                value = value - 65536
        return value


bus = smbus.SMBus(1) 	# or bus = smbus.SMBus(0) for older version boards
DeviceAddress = 0x68   # MPU6050 device address

while True:
	for num in range(2):
		if num == 0:
			GPIO.output(IMU1,GPIO.LOW)
			GPIO.output(IMU2,GPIO.HIGH)
			GPIO.output(IMU3,GPIO.HIGH)
		elif num == 1:
			GPIO.output(IMU1,GPIO.HIGH)
			GPIO.output(IMU2,GPIO.LOW)
			GPIO.output(IMU3,GPIO.HIGH)
		else:
			GPIO.output(IMU1,GPIO.HIGH)
			GPIO.output(IMU2,GPIO.HIGH)
			GPIO.output(IMU3,GPIO.LOW)

		MPU_Init()

		#Read Accelerometer raw value
		accX = read_raw_data(ACCEL_XOUT_H)
		accY = read_raw_data(ACCEL_YOUT_H)
		accZ = read_raw_data(ACCEL_ZOUT_H)

		#print(accX,accY,accZ)
		#print(math.sqrt((accY**2)+(accZ**2)))
		if (RestrictPitch):
			roll = math.atan2(accY,accZ) * radToDeg
			pitch = math.atan(-accX/math.sqrt((accY**2)+(accZ**2))) * radToDeg
		else:
			roll = math.atan(accY/math.sqrt((accX**2)+(accZ**2))) * radToDeg
			pitch = math.atan2(-accX,accZ) * radToDeg
		kalmanX[num].setAngle(roll)
		kalmanY[num].setAngle(pitch)
		gyroXAngle = roll
		gyroYAngle = pitch
		compAngleX = roll
		compAngleY = pitch

		timer = [time.time(),time.time(),time.time()]
		flag = 0

		if(flag >100): #Problem with the connection
			print("There is a problem with the connection")
			flag=0
			continue
		try:
			#Read Accelerometer raw value
			accX = read_raw_data(ACCEL_XOUT_H)
			accY = read_raw_data(ACCEL_YOUT_H)
			accZ = read_raw_data(ACCEL_ZOUT_H)

			#Read Gyroscope raw value
			gyroX = read_raw_data(GYRO_XOUT_H)
			gyroY = read_raw_data(GYRO_YOUT_H)
			gyroZ = read_raw_data(GYRO_ZOUT_H)

			dt = time.time() - timer[num]
			timer[num] = time.time()

			if (RestrictPitch):
				roll = math.atan2(accY,accZ) * radToDeg
				pitch = math.atan(-accX/math.sqrt((accY**2)+(accZ**2))) * radToDeg
			else:
				roll = math.atan(accY/math.sqrt((accX**2)+(accZ**2))) * radToDeg
				pitch = math.atan2(-accX,accZ) * radToDeg

			gyroXRate = gyroX/131
			gyroYRate = gyroY/131

			if (RestrictPitch):

				if((roll < -90 and kalAngleX[num] >90) or (roll > 90 and kalAngleX[num] < -90)):
					kalmanX[num].setAngle(roll)
					complAngleX = roll
					kalAngleX[num]   = roll
					gyroXAngle  = roll
				else:
					kalAngleX[num] = kalmanX[num].getAngle(roll,gyroXRate,dt)

				if(abs(kalAngleX[num])>90):
					gyroYRate  = -gyroYRate
					kalAngleY[num]  = kalmanY[num].getAngle(pitch,gyroYRate,dt)
			else:

				if((pitch < -90 and kalAngleY[num] >90) or (pitch > 90 and kalAngleY[num] < -90)):
					kalmanY[num].setAngle(pitch)
					complAngleY = pitch
					kalAngleY[num] = pitch
					gyroYAngle  = pitch
				else:
					kalAngleY[num] = kalmanY[num].getAngle(pitch,gyroYRate,dt)

				if(abs(kalAngleY[num])>90):
					gyroXRate  = -gyroXRate
					kalAngleX[num] = kalmanX[num].getAngle(roll,gyroXRate,dt)

			#angle = (rate of change of angle) * change in time
			gyroXAngle = gyroXRate * dt
			gyroYAngle = gyroYAngle * dt

			#compAngle = constant * (old_compAngle + angle_obtained_from_gyro) + constant * angle_obtained from accelerometer
			compAngleX = 0.93 * (compAngleX + gyroXRate * dt) + 0.07 * roll
			compAngleY = 0.93 * (compAngleY + gyroYRate * dt) + 0.07 * pitch

			if ((gyroXAngle < -180) or (gyroXAngle > 180)):
				gyroXAngle = kalAngleX
			if ((gyroYAngle < -180) or (gyroYAngle > 180)):
				gyroYAngle = kalAngleY

			#print("Angle X: " + str(kalAngleX[num])+"   " +"Angle Y: " + str(kalAngleY[num]))
			#print(str(roll)+"  "+str(gyroXAngle)+"  "+str(compAngleX)+"  "+str(kalAngleX)+"  "+str(pitch)+"  "+str(gyroYAngle)+"  "+str(compAngleY)+"  "+str(kalAngleY))
			time.sleep(0.005)
		except Exception as exc:
			print(exc)

	print("IMU 1: " + str(kalAngleX[0]) + ",  IMU2: " + str(kalAngleX[1]) + ", IMU3: " + str(kalAngleX[2]))