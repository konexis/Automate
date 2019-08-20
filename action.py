from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView
from PyQt5.QtCore import Qt


class ActionTreeWidget( QTreeWidget ):
    def __init__(self, parent=None):
        QTreeWidget.__init__(self, parent)
        #self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.header=QTreeWidgetItem(["Action","Setting"])
        self.setHeaderItem(self.header)
        self.setItemsExpandable(True)
        self.setAnimated(False)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        
        defaultParent=Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsEditable 
        defaultChild=Qt.ItemIsEnabled|Qt.ItemIsEditable 
        drag=Qt.ItemIsDragEnabled
        drop=Qt.ItemIsDropEnabled
        self.settings={
            "Action":(["root"],defaultParent|drag),
            "Setting":(["family"],defaultChild|drag|drop)
        }

        root=self.invisibleRootItem()
        root.setData(0,Qt.ToolTipRole,"root")

    def dragMoveEvent(self, event):
        role=Qt.ToolTipRole
        itemToDropIn = self.itemAt(event.pos())
        itemBeingDragged=self.currentItem()
        okList=self.settings[itemBeingDragged.data(0,role)][0]

        if itemToDropIn is None:
            itemToDropIn=self.invisibleRootItem()

        if itemToDropIn.data(0,role) in okList:
            super(ActionTreeWidget, self).dragMoveEvent(event)
            return
        else:
            # possible "next to drop target" case
            parent=itemToDropIn.parent()
            if parent is None:
                parent=self.invisibleRootItem()
            if parent.data(0,role) in okList:
                super(ActionTreeWidget, self).dragMoveEvent(event)
                return
        event.ignore()

    def dropEvent(self, event):
        role=Qt.ToolTipRole

        #item being dragged
        itemBeingDragged=self.currentItem()
        okList=self.settings[itemBeingDragged.data(0,role)][0]

        #parent before the drag
        oldParent=itemBeingDragged.parent()
        if oldParent is None:
            oldParent=self.invisibleRootItem()
        oldIndex=oldParent.indexOfChild(itemBeingDragged)

        #accept any drop
        super(ActionTreeWidget,self).dropEvent(event)

        #look at where itemBeingDragged end up
        newParent=itemBeingDragged.parent()
        if newParent is None:
            newParent=self.invisibleRootItem()

        if newParent.data(0,role) in okList:
            # drop was ok
            return
        else:
            # drop was not ok, put back the item
            newParent.removeChild(itemBeingDragged)
            oldParent.insertChild(oldIndex,itemBeingDragged)
    
    def addItem(self,strings,category,parent=None):
        if category not in self.settings:
            print("unknown categorie" +str(category))
            return False
        if parent is None:
            parent=self.invisibleRootItem()

        item=QTreeWidgetItem(parent,strings)
        item.setData(0,Qt.ToolTipRole,category)

        item.setExpanded(False)
        item.setFlags(self.settings[category][1])
        return item
    

        
    def getItems(self):
        threeList = []
        root = self.invisibleRootItem()
        child_count = root.childCount()
        for i in range(child_count):
            threeList.append([root.child(i).text(0)])
            for j in range(100):
                try:
                    threeList[i].append(root.child(i).child(j).text(0))
                    threeList[i].append(root.child(i).child(j).text(1))
                except: break
        return threeList
