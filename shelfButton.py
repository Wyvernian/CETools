from CETools.windows import main

if __name__ == "__main__":
    try:
        CETools.close()
        CETools.deleteLater()
    except:
        pass
    CETools = main.mainWindow()

    try:
        CETools.create()
        CETools.show(dockable=True)

    except:
        CETools.close()
        CETools.deleteLater()
