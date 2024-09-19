#!/usr/bin/env python3

import datetime
import logging
import re
import struct
import wx

# Default values
DEFAULT_VERSION = 12
DEFAULT_FIRMWARE = 7
DEFAULT_BODY = 9
DEFAULT_CONNECT = 6
DEFAULT_DISPLAY = "unknown"
DEFAULT_COLOR = "transparent"
DEFAULT_REGION = "world"
DEFAULT_NAME = "kalicyh"
DEFAULT_FILENAME = "kalicyh_otp"

OTP_MAGIC = 0xBABE
OTP_VERSION = 0x02
OTP_RESERVED = 0x00

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

OTP_DISPLAYS = {
    "unknown": 0x00,
    "erc": 0x01,
    "mgg": 0x02,
}


class OTPApp(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(OTPApp, self).__init__(*args, **kwargs)

        # Initialize logging
        self.logger = logging.getLogger()
        logging.basicConfig(level=logging.INFO)

        # Bind the close event
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # GUI Elements
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Create a FlexGridSizer with 2 columns
        grid = wx.FlexGridSizer(rows=0, cols=2, vgap=10, hgap=10)
        grid.AddGrowableCol(1, 1)  # Make the second column growable

        # Create and add input fields
        self.version = wx.TextCtrl(panel, value=str(DEFAULT_VERSION), style=wx.TE_RIGHT)
        self.firmware = wx.TextCtrl(panel, value=str(DEFAULT_FIRMWARE), style=wx.TE_RIGHT)
        self.body = wx.TextCtrl(panel, value=str(DEFAULT_BODY), style=wx.TE_RIGHT)
        self.connect = wx.TextCtrl(panel, value=str(DEFAULT_CONNECT), style=wx.TE_RIGHT)
        self.display = wx.ComboBox(panel, choices=list(OTP_DISPLAYS.keys()), style=wx.CB_READONLY)
        self.display.SetValue(DEFAULT_DISPLAY)

        self.color = wx.ComboBox(panel, choices=list(OTP_COLORS.keys()), style=wx.CB_READONLY)
        self.color.SetValue(DEFAULT_COLOR)
        self.region = wx.ComboBox(panel, choices=list(OTP_REGIONS.keys()), style=wx.CB_READONLY)
        self.region.SetValue(DEFAULT_REGION)
        self.name = wx.TextCtrl(panel, value=DEFAULT_NAME, style=wx.TE_RIGHT)

        self.output_file = wx.TextCtrl(panel, value=DEFAULT_FILENAME, style=wx.TE_RIGHT)
        browse_button = wx.Button(panel, label="浏览")
        browse_button.Bind(wx.EVT_BUTTON, self.on_browse)

        generate_button = wx.Button(panel, label="生成文件")
        generate_button.Bind(wx.EVT_BUTTON, self.on_generate)

        # Add labels and input fields to the grid
        grid.Add(wx.StaticText(panel, label="Version:"), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.version, flag=wx.EXPAND)
        grid.Add(wx.StaticText(panel, label="Firmware:"), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.firmware, flag=wx.EXPAND)
        grid.Add(wx.StaticText(panel, label="Body:"), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.body, flag=wx.EXPAND)
        grid.Add(wx.StaticText(panel, label="Connect:"), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.connect, flag=wx.EXPAND)
        grid.Add(wx.StaticText(panel, label="显示屏型号:"), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.display, flag=wx.EXPAND)

        grid.Add(wx.StaticText(panel, label="颜色:"), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.color, flag=wx.EXPAND)
        grid.Add(wx.StaticText(panel, label="地区:"), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.region, flag=wx.EXPAND)
        grid.Add(wx.StaticText(panel, label="名称:"), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.name, flag=wx.EXPAND)

        grid.Add(wx.StaticText(panel, label="输出文件:"), flag=wx.ALIGN_CENTER_VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.output_file, proportion=1, flag=wx.EXPAND)
        hbox.Add(browse_button, flag=wx.LEFT, border=5)
        grid.Add(hbox, flag=wx.EXPAND)

        vbox.Add(grid, flag=wx.ALL | wx.EXPAND, border=10)
        vbox.Add(generate_button, flag=wx.ALL | wx.CENTER, border=10)

        panel.SetSizer(vbox)
        
        # Adjust layout and fit content
        vbox.Fit(panel)
        panel.Layout()
        self.Fit()

        self.SetTitle("Flipper OTP 生成")
        self.Centre()

    def on_close(self, event):
        # Perform any cleanup tasks here if necessary
        self.Destroy()  # Destroys the frame and closes the application

    def on_browse(self, event):
        with wx.FileDialog(self, "保存输出文件", wildcard="Binary files (*.bin)|*.bin",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            self.output_file.SetValue(fileDialog.GetPath())

    def on_generate(self, event):
        try:
            self._processFirstArgs()
            self._processSecondArgs()

            output_file = self.output_file.GetValue()
            if not output_file.endswith(".bin"):
                output_file += ".bin"

            if not output_file:
                wx.MessageBox("请指定一个输出文件。", "Error", wx.OK | wx.ICON_ERROR)
                return

            self.logger.info("Generating OTP")
            # 合并生成的二进制数据
            with open(output_file, "wb") as file:
                file.write(self._packFirst() + self._packSecond())

            wx.MessageBox(f"生成文件: {output_file}",
                        "成功", wx.OK | wx.ICON_INFORMATION)

        except Exception as e:
            wx.MessageBox(str(e), "Error", wx.OK | wx.ICON_ERROR)


    def _processFirstArgs(self):
        if self.display.GetValue() not in OTP_DISPLAYS:
            raise ValueError(f"Invalid display. Use one of {list(OTP_DISPLAYS.keys())}")
        self.display_value = OTP_DISPLAYS[self.display.GetValue()]

    def _processSecondArgs(self):
        if self.color.GetValue() not in OTP_COLORS:
            raise ValueError(f"Invalid color. Use one of {list(OTP_COLORS.keys())}")
        self.color_value = OTP_COLORS[self.color.GetValue()]

        if self.region.GetValue() not in OTP_REGIONS:
            raise ValueError(f"Invalid region. Use one of {list(OTP_REGIONS.keys())}")
        self.region_value = OTP_REGIONS[self.region.GetValue()]

        name = self.name.GetValue()
        if len(name) > 8:
            raise ValueError("名字太长，最长8个字符")
        if re.match(r"^[a-zA-Z0-9.]+$", name) is None:
            raise ValueError("名称包含不正确的符号。仅允许使用 a-zA-Z0-9。")

    def _packFirst(self):
        return struct.pack(
            "<" "HBBL" "BBBBBBH",
            OTP_MAGIC,
            OTP_VERSION,
            OTP_RESERVED,
            int(datetime.datetime.now().timestamp()),
            int(self.version.GetValue()),
            int(self.firmware.GetValue()),
            int(self.body.GetValue()),
            int(self.connect.GetValue()),
            self.display_value,
            OTP_RESERVED,
            OTP_RESERVED,
        )

    def _packSecond(self):
        return struct.pack(
            "<" "BBHL" "8s",
            self.color_value,
            self.region_value,
            OTP_RESERVED,
            OTP_RESERVED,
            self.name.GetValue().encode("ascii"),
        )


def main():
    app = wx.App(False)
    frame = OTPApp(None)
    frame.Show(True)
    app.MainLoop()


if __name__ == "__main__":
    main()
