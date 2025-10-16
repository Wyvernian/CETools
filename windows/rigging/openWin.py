import CETools.windows.rigging.main as main


def load_window():
    try:
        CErg.close()
        CErg.deleteLater()
    except:
        pass
    CErg = main.MainWindow()
    try:
        CErg.create()
        CErg.show(dockable=True)

    except:
        CErg.close()
        CErg.deleteLater()
