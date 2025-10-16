import CETools.windows.matchmove.main as main


def load_window():
    try:
        CEmm.close()
        CEmm.deleteLater()
    except:
        pass
    CEmm = main.MainWindow()
    try:
        CEmm.create()
        CEmm.show(dockable=True)

    except:
        CEmm.close()
        CEmm.deleteLater()
