import CETools.windows.animation.main as main


def load_window():
    try:
        CEan.close()
        CEan.deleteLater()
    except:
        pass
    CEan = main.MainWindow()
    try:
        CEan.create()
        CEan.show(dockable=True)

    except:
        CEan.close()
        CEan.deleteLater()
