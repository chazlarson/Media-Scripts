#!/usr/bin/env python
import wx
import wx.adv
from wx.adv import Wizard as wizmod
#import images
from wx.adv import WizardPage, WizardPageSimple
import os.path
padding = 5

def onPlexTest(event):
	print( "PlexTest button pressed.")

class wizard_page(wx.adv.WizardPage):
    ''' An extended panel obj with a few methods to keep track of its siblings.
        This should be modified and added to the wizard.  Season to taste.'''
    def __init__(self, parent, title):
        WizardPage.__init__(self, parent)
        self.next = self.prev = None
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, -1, title)
        title.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.sizer.Add(title, 0, wx.ALIGN_LEFT|wx.ALL, padding)
        self.sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, padding)
        self.SetSizer(self.sizer)

    def add_stuff(self, stuff):
        '''Add aditional widgets to the bottom of the page'''
        self.sizer.Add(stuff, 0, wx.EXPAND|wx.ALL, padding)

    def SetNext(self, next):
        '''Set the next page'''
        self.next = next

    def SetPrev(self, prev):
        '''Set the previous page'''
        self.prev = prev

    def GetNext(self):
        '''Return the next page'''
        return self.next

    def GetPrev(self):
        '''Return the previous page'''
        return self.prev


class wizard(wx.adv.Wizard):
    '''Add pages to this wizard object to make it useful.'''
    def __init__(self, title, img_filename=""):
        # img could be replaced by a py string of bytes
        if img_filename and os.path.exists(img_filename):
                img = wx.Bitmap(img_filename)
        else:   img = wx.NullBitmap
        wx.adv.Wizard.__init__(self, None, -1, title, img)
        self.pages = []
        # Lets catch the events
        self.Bind(wx.adv.EVT_WIZARD_PAGE_CHANGED, self.on_page_changed)
        self.Bind(wx.adv.EVT_WIZARD_PAGE_CHANGING, self.on_page_changing)
        self.Bind(wx.adv.EVT_WIZARD_CANCEL, self.on_cancel)
        self.Bind(wx.adv.EVT_WIZARD_FINISHED, self.on_finished)

    def add_page(self, page):
        '''Add a wizard page to the list.'''
        if self.pages:
            previous_page = self.pages[-1]
            page.SetPrev(previous_page)
            previous_page.SetNext(page)
        self.pages.append(page)

    def run(self):
        self.RunWizard(self.pages[0])

    def on_page_changed(self, evt):
        '''Executed after the page has changed.'''
        if evt.GetDirection():  dir = "forward"
        else:                   dir = "backward"
        page = evt.GetPage()
        print ("page_changed: %s, %s\n" % (dir, page.__class__))

    def on_page_changing(self, evt):
        '''Executed before the page changes, so we might veto it.'''
        if evt.GetDirection():  dir = "forward"
        else:                   dir = "backward"
        page = evt.GetPage()
        print ("page_changing: %s, %s\n" % (dir, page.__class__))

    def on_cancel(self, evt):
        '''Cancel button has been pressed.  Clean up and exit without continuing.'''
        page = evt.GetPage()
        print ("on_cancel: %s\n" % page.__class__)

        # # Prevent cancelling of the wizard.
        # if page is self.pages[0]:
        #     wx.MessageBox("Cancelling on the first page has been prevented.", "Sorry")
        #     evt.Veto()

    def on_finished(self, evt):
        '''Finish button has been pressed.  Clean up and exit.'''
        print ("OnWizFinished\n")


if __name__ == '__main__':

    app = wx.App()  # Start the application

    # Create wizard and add any kind pages you'd like
    mywiz = wizard('Simple Wizard', img_filename='wiz.png')

    page1 = wizard_page(mywiz, 'Plex Server Details')  # Create a first page
    page1.add_stuff(wx.StaticText(page1, -1, 'server'))
    page1.add_stuff(wx.TextCtrl(page1,-1,'plexserver'))
    page1.add_stuff(wx.StaticText(page1, -1, 'token'))
    page1.add_stuff(wx.TextCtrl(page1,-1,'####################'))
    page1.add_stuff(wx.StaticText(page1, -1, 'port'))
    page1.add_stuff(wx.TextCtrl(page1,-1,'32400'))
    page1.add_stuff(wx.StaticText(page1, -1, 'timeout'))
    page1.add_stuff(wx.TextCtrl(page1,-1,'60'))
    page1.add_stuff(wx.CheckBox(page1,-1,'secure',(35,40),(150,20)))
    page1.add_stuff(wx.CheckBox(page1,-1,'clean_bundles',(35,40),(150,20)))
    page1.add_stuff(wx.CheckBox(page1,-1,'empty_trash',(35,40),(150,20)))
    page1.add_stuff(wx.CheckBox(page1,-1,'optimize',(35,40),(150,20)))
    page1.add_stuff(wx.Button(page1,-1,"Test"))
    mywiz.add_page(page1)

    page2 = wizard_page(mywiz, 'TMDB API Key')  # Create a first page
    page2.add_stuff(wx.StaticText(page2, -1, 'TMDB API Key'))
    page2.add_stuff(wx.TextCtrl(page2,-1,'TMDB_API_KEY',))
    page2.add_stuff(wx.StaticText(page2, -1, 'language'))
    page2.add_stuff(wx.TextCtrl(page2,-1,'en'))
    page2.add_stuff(wx.Button(page2,-1,"Test"))
    mywiz.add_page(page2)

    page3 = wizard_page(mywiz, 'OMDB API Key')  # Create a first page
    page3.add_stuff(wx.StaticText(page3, -1, 'OMDB API Key'))
    page3.add_stuff(wx.TextCtrl(page3,-1,'OMDB_API_KEY',))
    page3.add_stuff(wx.Button(page3,-1,"Test"))
    mywiz.add_page(page3)

    page4 = wizard_page(mywiz, 'tautulli Details')  # Create a first page
    page4.add_stuff(wx.StaticText(page4, -1, 'server'))
    page4.add_stuff(wx.TextCtrl(page4,-1,'tautulliserver',))
    page4.add_stuff(wx.StaticText(page4, -1, 'port'))
    page4.add_stuff(wx.TextCtrl(page4,-1,'8181'))
    page4.add_stuff(wx.StaticText(page4, -1, 'api key'))
    page4.add_stuff(wx.TextCtrl(page4,-1,'################################'))
    page4.add_stuff(wx.CheckBox(page4,-1,'secure',(35,40),(150,20)))
    page4.add_stuff(wx.Button(page4,-1,"Test"))
    mywiz.add_page(page4)

    page5 = wizard_page(mywiz, 'Notifiarr API Key')  # Create a first page
    page5.add_stuff(wx.StaticText(page5, -1, 'Notifiarr API Key'))
    page5.add_stuff(wx.TextCtrl(page5,-1,'NOTIFIARR_API_KEY',))
    page5.add_stuff(wx.Button(page5 ,-1,"Test"))
    mywiz.add_page(page5)

    page6 = wizard_page(mywiz, 'AniDB Login')  # Create a first page
    page6.add_stuff(wx.StaticText(page6, -1, 'AniDB username'))
    page6.add_stuff(wx.TextCtrl(page6,-1,'######'))
    page6.add_stuff(wx.StaticText(page6, -1, 'AniDB password'))
    page6.add_stuff(wx.TextCtrl(page6,-1,'######'))
    page6.add_stuff(wx.Button(page6 ,-1,"Test"))
    mywiz.add_page(page6)

    page1 = wizard_page(mywiz, 'Global Radarr Details')  # Create a first page
    page1.add_stuff(wx.StaticText(page1, -1, 'server'))
    page1.add_stuff(wx.TextCtrl(page1,-1,'radarrserver'))
    page1.add_stuff(wx.StaticText(page1, -1, 'token'))
    page1.add_stuff(wx.TextCtrl(page1,-1,'####################'))
    page1.add_stuff(wx.StaticText(page1, -1, 'port'))
    page1.add_stuff(wx.TextCtrl(page1,-1,'7878'))
    page1.add_stuff(wx.CheckBox(page1,-1,'secure',(35,40),(150,20)))

    page1.add_stuff(wx.StaticText(page1, -1, 'availability'))
    page1.add_stuff(wx.TextCtrl(page1,-1,'announced'))

    page1.add_stuff(wx.CheckBox(page1,-1,'add_missing',(35,40),(150,20)))
    page1.add_stuff(wx.CheckBox(page1,-1,'add_existing',(35,40),(150,20)))
    page1.add_stuff(wx.CheckBox(page1,-1,'monitor',(35,40),(150,20)))
    page1.add_stuff(wx.CheckBox(page1,-1,'search',(35,40),(150,20)))

    page1.add_stuff(wx.Button(page1,-1,"Test"))
    mywiz.add_page(page1)


# radarr:
#   root_folder_path: S:/Movies
#   availability: announced
#   quality_profile: HD-1080p
#   tag:
#   radarr_path:
#   plex_path:
# sonarr:
#   url: http://192.168.1.12:8989
#   token: ################################
#   add_missing: false
#   add_existing: false
#   root_folder_path: "S:/TV Shows"
#   monitor: all
#   quality_profile: HD-1080p
#   language_profile: English
#   series_type: standard
#   season_folder: true
#   tag:
#   search: false
#   cutoff_search: false
#   sonarr_path:
#   plex_path:
# trakt:
#   client_id: ################################################################
#   client_secret: ################################################################
#   authorization:
#     # everything below is autofilled by the script
#     access_token:
#     token_type:
#     expires_in:
#     refresh_token:
#     scope: public
#     created_at:
# mal:
#   client_id: ################################
#   client_secret: ################################################################
#   authorization:
#     # everything below is autofilled by the script
#     access_token:
#     token_type:
#     expires_in:
#     refresh_token:

    mywiz.run() # Show the main window

    # Cleanup
    mywiz.Destroy()
    #del app
    app.MainLoop()
    del app