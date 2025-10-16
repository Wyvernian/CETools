import CETools.windows.lookdev.main as main


def load_window():
    try:
        CEld.close()
        CEld.deleteLater()
    except:
        pass
    CEld = main.MainWindow()
    try:
        CEld.create()
        CEld.show(dockable=True)

    except:
        CEld.close()
        CEld.deleteLater()
