import CETools.windows.modelling.main as main


def load_window():
    try:
        CEmd.close()
        CEmd.deleteLater()
    except:
        pass
    CEmd = main.MainWindow()
    try:
        CEmd.create()
        CEmd.show(dockable=True)

    except:
        CEmd.close()
        CEmd.deleteLater()
