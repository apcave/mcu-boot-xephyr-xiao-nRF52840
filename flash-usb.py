from pynrfjprog import LowLevel
api = LowLevel.API()
api.open()
api.connect_to_emu_without_snr()
api.program_file('your_firmware.hex')
api.sys_reset()
api.close()