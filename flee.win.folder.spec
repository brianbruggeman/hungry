# -*- mode: python -*-
a = Analysis(['flee.py'],
             pathex=['C:\\Users\\Bix\\repos\\mine\\gamejam\\hungry'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
a.datas += [("resources/Tahoma.ttf", "resources/Tahoma.ttf", "resources")]
a.datas += [("resources/player.png", "resources/player.png", "resources")]
a.datas += [("resources/zombie.ttf", "resources/zombie.png", "resources")]             
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='flee.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='flee')
