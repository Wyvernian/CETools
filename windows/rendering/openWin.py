import CETools.windows.rendering.main as main


def load_window():
    try:
        CErd.close()
        CErd.deleteLater()
    except:
        pass
    CErd = main.MainWindow()
    try:
        CErd.create()
        CErd.show(dockable=True)

    except:
        CErd.close()
        CErd.deleteLater()
