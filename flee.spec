# -*- mode: python -*-
a = Analysis(['flee.py'],
             pathex=['resources', '/Users/brianbruggeman/repos/mine/gamejam/bacongamejam07'],
             hiddenimports=['OpenGL', 'random'],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='flee',
          debug=True,
          strip=None,
          upx=True,
          console=False , icon='resources/flee.ico')
app = BUNDLE(exe,
             name='flee.app',
             icon='resources/flee.ico')
