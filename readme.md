# Install VirtualBox

[ArchLinux Wiki](https://wiki.archlinux.org/index.php/VirtualBox#Installation_steps_for_Arch_Linux_hosts)

# Create Windows 7 virtual machine

## Use windows7-ultimate-with-sp1-dvd.iso

Not recommended.

## Download free virtual machine from [microsoft](https://developer.microsoft.com/en-us/microsoft-edge/tools/vms/)

Select virtual machine: "IE11 on Win7 (x86)" ~~or "IE11 on Win81 (x86)", "MSEdge on Win10 (x64) Stable 1809"~~

Default password "Passw0rd!"

```
[$] sha1sum IE11.Win7.VirtualBox.ova
25778f2c04f0badb688bfe49da3834517a8e7f96  IE11.Win7.VirtualBox.ova
```

Issue: 右键打开 ova 文件，导入出错 `NS_ERROR_INVALID_ARG (0x80070057)`，解决办法:
[命令行绝对路径导入 ova](https://www.cnblogs.com/cocowool/archive/2009/09/23/1572852.html)

```bash
vmname="Win7"
## VBoxManage list systemproperties | grep 'machine folder'
vmfolder="$HOME/VirtualBox VMs"
VBoxManage import $PWD/IE11.Win7.VirtualBox.ova --vsys 0 \
    --vmname "$vmname" \
    --settingsfile "$vmfolder/$vmname/$vmname.vbox" \
    --cpus 2 \
    --memory 2560 \
    --unit 11 --disk "$vmfolder/$vmname/$vmname-disk.vdi"
```

* [modify virtual machine](https://docs.oracle.com/cd/E97728_01/E97727/html/vboxmanage-modifyvm.html)
    - 显示 -> 显存、控制器、加速
      ```bash
      VBoxManage modifyvm "$vmname" \
        --vram 256 \
        --graphicscontroller vboxsvga \
        --accelerate3d on \
        --accelerate2dvideo on
      ```
    - 存储加一光驱
    - 共享文件夹加一固定分配 


# Settings

## 基本项

* Windows Update 关闭自动更新, 手动安装中文语言包

* 声卡驱动: Device Manager -> Update Driver

* vbox 分配光驱, Safe Mode 安装增强功能
    - [Windows 7 Enterprise Safe Mode Problems](https://social.technet.microsoft.com/Forums/windows/en-US/ef0e41cb-955b-4a29-9318-2c56a198d746/windows-7-enterprise-safe-mode-problems?forum=w7itproperf)
    - Boot -> F8 -> Use:
        + Safe Mode: fail and restart
        + Safe Mode with Networking: fail and restart
        + Directory Services Restore Mode: login Safe Mode
    - asks “would you like to install basic Direct3D support instead?” Click NO
    - Direct3D on, 有些软件显示会出现黑块, 需关闭硬件图形加速, 如:
        + IE11, Options -> Advanced -> Accelerated graphics -> Use software rendering
        + Office 2016, 设置见下节

* 更改用户名、密码、主题

* 添加共享文件夹: Map Network Drive `Z:`

* 时区 +8, 时间显示 HH:mm

* 添加 [Rime输入法](https://rime.im), ~~[微软拼音输入法 2010](https://www.microsoft.com/zh-cn/download/details.aspx?id=28969)~~

* 检查启动项目: msconfig -> Startup, Disable `BGInfo`

## 安装 office 2016

* 下载 `cn_office_professional_plus_2016_x86_x64_dvd_6969182.iso`
* ~~下载 [Virtual CD-ROM Control Panel](https://www.microsoft.com/en-us/download/details.aspx?id=38780)~~
* 下载 [officedeploymenttool](https://docs.microsoft.com/zh-cn/deployoffice/overview-of-the-office-2016-deployment-tool), 编写 `configuration-Office2016.xml`

1. ~~VCdControlTool -> Add Drive "X:", 与 configuration 中 SourcePath 相同.~~
   Vbox 分配光驱 D盘挂载 office iso.

2. 管理员运行 powershell

```
cd Z:\path\to\officedeploymenttool
.\setup.exe /configure .\configuration-Office2016.xml
```

3. 手动卸载 OneDrive

4. Fix black screen in office, when vbox Direct3D support is ON.
    - Turn off Hardware Graphics Acceleration in Office 2016.
    - 文件 -> 选项 -> 高级 -> 显示 -> 禁用硬件图形加速、禁用幻灯片放映硬件图形加速

## 激活

* ~~Use `Windows_7_Enterprise_Downgrade` and your KEY~~
* Use host bios SLIC, [/sys/firmware/acpi/tables/SLIC](https://www.virtualbox.org/ticket/9231)
* Use KMS

## ZJU RVPN

Install `EasyConnect`


## Disk Cleanup

1. 禁用虚拟内存

2. 磁盘清理

3. [Compact virtual disks](https://wiki.archlinux.org/index.php/VirtualBox#Compact_virtual_disks)
   * [sdelete](https://docs.microsoft.com/zh-cn/sysinternals/downloads/sdelete)
   * `sdelete -s -z C:`

```
VBoxManage modifyhd "$vmfolder/$vmname/$vmname-disk.vdi" --compact
```

## Backup

导出虚拟电脑到 `Win7-v1.VirtualBox.ova` (13.6G vdi -> 5.6G ova).


# Arch Host

## 桥接网卡, 分享网络

* Host 可 ssh 登录 win7(自带sshd服务)

  添加 Host `～/.ssh/id_rsa.pub` 到 win7 IEUser 的 `%HOMEDRIVE%%HOMEPATH%\.ssh\authorized_keys`

* 通过 rvpn 接口, 登录校内服务器

  编辑 `～/.ssh/config`
  ```
  ### vitrualbox bridge
  Host    win7.vbox
      HostName 192.168.xx.xx
      User IEUser
      Port 22
  
  Host    xxx
      HostName xx.xx.xx.xx
      ProxyCommand ssh -W %h:%p win7.vbox
  ```

## AwesomeWM

* ~~[ref](http://kissmyarch.blogspot.com/2012/01/hiding-menu-and-statusbar-of-virtualbox.html)~~

* 快捷键使用
    - 鼠标集成 "Auto Capture Keyboard" on
    - 虚拟机内切换到 awesome 键盘控制, 需先按主机键 `右 ctrl`, 再按 awesome 快捷键, 如
        + 切换到右 tag, 先 `右 ctrl`， 再 `Super+右`
        + 全屏虚拟机窗口, 先点窗口, 再 `右 ctrl`, 最后 `Super+F`
    - 虚拟机独占一个 awesome tag 并全屏显示
        + 先虚拟机全屏模式 `右 ctrl+F`
        + 再 awesome 全屏虚拟机窗口, 需两次生效, 即 2 x (点窗口 + `右 ctrl` + `Super+F`)
    - 退出虚拟机全屏显示 `右 ctrl+F`


# Advanced Topic: PCI Passthrough

* http://www.virtualbox.org/manual/ch09.html#pcipassthrough
* Arch `Oracle VM VirtualBox and Extension Packs` -> `aur/virtualbox-ext-oracle`

## GPU

```
VBoxManage modifyvm "$vmname" --pciattach XX:YY.Z@xx:yy.z
VBoxManage modifyvm "$vmname" --pcidetach XX:YY.Z
```

1. Error `Host PCI attachment only supported with ICH9 chipset`

Fix: 主板芯片组设置为 ICH9, `VBoxManage modifyvm "$vmname" --chipset ich9`

2. Issue: recognized as "3d video controller", cannot install gpu driver!

* [ref1](https://www.reddit.com/r/linuxquestions/comments/5k3q7s/qemu_gpu_passthrough_not_recognized_by_windows/)
* [ref2](https://wiki.archlinux.org/index.php/PCI_passthrough_via_OVMF#%22Error_43:_Driver_failed_to_load%22_on_Nvidia_GPUs_passed_to_Windows_VMs)
