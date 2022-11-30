robel-dclaw

## DClaw環境
![Screenshot from 2022-11-30 20-19-12](https://user-images.githubusercontent.com/49630508/204783027-c0209e65-b207-4086-b2c2-5f77ba115652.png)
![Screenshot from 2022-08-20 02-22-30](https://user-images.githubusercontent.com/49630508/185674226-85950dba-7e45-49fa-9070-62758f353227.png)


## バルブの目印
- half-length of the cylinder = 0.005[m]
- full-length of the cylinder = 0.01[m] = 1[cm]
- 従って，目印の幅は1[cm]


## EnvStateの定義

### robot_position
- 9次元
- インデックス[0, 1, 2]：1本目の指の第一関節，第二関節，第三関節の関節角度
- インデックス[3, 4, 5]：2本目の指の ''
- インデックス[6, 7, 8]：3本目の指の ''

### object_position
- 1次元
- バルブの関節角度

### robot_velocity（今回は使わないかもしれません）
- 9次元
- インデックス[0, 1, 2]：1本目の指の第一関節，第二関節，第三関節の関節速度
- インデックス[3, 4, 5]：2本目の指の ''
- インデックス[6, 7, 8]：3本目の指の ''


### object_velocity
- 1次元
- バルブの関節速度


### force
- 9次元
- 指先に設置してあるフォースセンサの値
- インデックス[0, 1, 2]：1本目の指の指先に設置してあるフォースセンサの値
- インデックス[3, 4, 5]：2本目の ''
- インデックス[6, 7, 8]：3本目の ''


## 制御入力の定義
### ctrl
- 9次元
- [0, 1, 2] : 1本目の指の第一関節，第二関節，第三関節の目標関節位置
- [3, 4, 5] : 2本目の指の ''
- [6, 7, 8] : 3本目の指の ''
