def setStylesheet(self,bannerDir):
    stylesheet = ("""
    MainWindow {
    
        background-image: url("%s/banner.jpg"); 
        background-repeat: no-repeat; 
        background-position: top left;
        background-color: #161616;

    }
    
    QPushButton {
        border: 0px solid;
        background-color: #161616;
        font-weight: bold;
        font-family: verdana;
        font-size: 10px;
        color: rgb(150,150,150);
    }

    QPushButton:hover {
        color: white;

    }
    
    QPushButton:disabled {
        color: rgb(50,50,50);
    }

    
    QWidget {
        background-color: #161616;
        border: 0px solid;
    }
    
    QScrollBar {
        background-color: #161616;
        border-radius: 5px    
    }
    
    QScrollBar::handle {
        background-color: rgb(100,100,100);
        border-radius: 2px    
    }
    
     QScrollBar:horizontal {
        height: 5px;
    }

    QScrollBar:vertical {
        width: 5px;
    }
    

    
    CheckboxGroup {
        color: rgb(100, 0, 0);
    }
    
    QGroupBox {
        border: 1px solid;
        border-color: rgba(0, 0, 0, 64);
        border-radius: 6px;
        background-color: rgb(78, 80, 82);
        font-weight: bold;
        font: bold 15px;
        }
        QGroupBox::title {
        subcontrol-origin: margin;
        left: 6px;
        top: 4px;
        }
        QGroupBox::indicator:checked {
        image: url(:/arrowDown.png);
        }
        QGroupBox::indicator:unchecked {
        image: url(:/arrowRight.png);
        }
    """ % bannerDir)
    print("Stylesheet set!")
    
    self.setStyleSheet(stylesheet)
    
    