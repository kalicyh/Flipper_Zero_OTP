# Flipper Zero OTP

旨在为非官方设备提供官方的OTP
OTP只能写入一次
无法二次修改
如果想更改需要更换芯片

## 定制化

- 使用自己想要的名称
- 不同的颜色对应的手机app内的Flipper Zero颜色也不一样

## 参数

可以修改的
```
color: 颜色（必须提供，需从 OTP_COLORS 字典中选择）
region: 区域（必须提供，需从 OTP_REGIONS 字典中选择）
name: 名称（必须提供，长度不超过 8 个字符，仅支持 a-zA-Z0-9）
```

```
OTP_COLORS = {
    "unknown": 0x00,
    "black": 0x01,
    "white": 0x02,
    "transparent": 0x03,
}

OTP_REGIONS = {
    "unknown": 0x00,
    "eu_ru": 0x01,
    "us_ca_au": 0x02,
    "jp": 0x03,
    "world": 0x04,
}
```

不能动的，需要使用默认提供的

```
version: 版本号（在PCB主板上）
firmware: 固件版本号
body: 机壳版本号
connect: 连接版本号
display: 显示类型
```

## 打包命令

```sh
pyinstaller --onefile --noconsole --icon=flipper.ico --name='qFlipper OTP' main.py
```