"""
# SAPHana
# Author:       Fabian Herschel, 2015
# License:      GNU General Public License (GPL)
# Copyright:    (c) 2015-2016 SUSE Linux GmbH
# Copyright:    (c) 2017-2021 SUSE LLC

SAPHanaSrMultiTarget needs SAP HANA 2.0 SPS4 (2.00.040.00) as minimum version
"""
import os

try:
    from hdb_ha_dr.client import HADRBase
except ImportError as e:
    print("Module HADRBase not found - running outside of SAP HANA? - {0}".format(e))

"""
Only for SAP HANA >= 2.0 SPS3

To use this HA/DR hook provide please add the following lines (or similar) to your global.ini:
    [ha_dr_provider_SAPHanaSrMultiTarget]
    provider = SAPHanaSrMultiTarget
    path = /usr/share/SAPHanaSR-ScaleOut
    cib_access = all-on
    execution_order = 1

    [trace]
    ha_dr_saphanasr = info
"""
fhSRHookVersion = "0.181.0.0110.1727"
srHookGen = "2.1"
cib_access_dflt = "all-on"

try:
    class SAPHanaSrMultiTarget(HADRBase):

        def __init__(self, *args, **kwargs):
            # delegate construction to base class
            super(SAPHanaSrMultiTarget, self).__init__(*args, **kwargs)
            method = "init"
            if self.config.hasKey("cib_access"):
                self.cib_access = self.config.get("cib_access")
                # first step, should be removed later
                if self.cib_access != "site-on":
                    self.cib_access = "all-on"
            else:
                self.cib_access = cib_access_dflt
            self.tracer.info("{0}.{1}() version {2}, hookGeneration {3}, cib_access {4}".format(self.__class__.__name__, method, fhSRHookVersion, srHookGen, self.cib_access))
            mySID = os.environ.get('SAPSYSTEMNAME')
            mysid = mySID.lower()
            myCMD = "sudo /usr/sbin/crm_attribute -n hana_{1}_gsh -v {0}  -l reboot".format(srHookGen, mysid)
            rc = os.system(myCMD)
            myMSG = "CALLING CRM: <{0}> rc={1}".format(myCMD, rc)
            self.tracer.info("{0}.{1}() {2}\n".format(self.__class__.__name__, method, myMSG))
            self.tracer.info("{0}.{1}() Running srHookGeneration {2}, see attribute hana_{3}_gsh too\n".format(self.__class__.__name__, method, srHookGen, mysid))

            # check if multi-target support attribute exists
            mts = "true"
            myCMD = "sudo /usr/sbin/crm_attribute -n hana_%s_glob_mts -G" % (mysid)
            rc = os.system(myCMD)
            if rc != 0:
                # multi-target support attribute not found, create it
                myCMD = "sudo /usr/sbin/crm_attribute -n hana_{0}_glob_mts -v {1} -t crm_config -s SAPHanaSR".format(mysid, mts)
                rc = os.system(myCMD)
                myMSG = "CALLING CRM: <{0}> rc={1}".format(myCMD, rc)
                self.tracer.info("{0}.{1}() {2}\n".format(self.__class__.__name__, method, myMSG))

        def about(self):
            method = "about"
            self.tracer.info("{0}.{1}() version {2}".format(self.__class__.__name__, method, fhSRHookVersion))
            return {"provider_company": "SUSE",
                    "provider_name": "SAPHanaSrMultiTarget",  # class name
                    "provider_description": "Inform Cluster about SR state",
                    "provider_version": "1.0"}

        def startup(self, hostname, storage_partition, sr_mode, **kwargs):
            method = "startup"
            self.tracer.debug("enter startup hook; {0}".format(locals()))
            self.tracer.debug(self.config.toString())
            self.tracer.info("leave startup hook")
            return 0

        def shutdown(self, hostname, storage_partition, sr_mode, **kwargs):
            method = "shutdown"
            self.tracer.debug("enter shutdown hook; {0}".format(locals()))
            self.tracer.debug(self.config.toString())
            self.tracer.info("leave shutdown hook")
            return 0

        def failover(self, hostname, storage_partition, sr_mode, **kwargs):
            method = "failover"
            self.tracer.debug("enter failover hook; {0}".format(locals()))
            self.tracer.debug(self.config.toString())
            self.tracer.info("leave failover hook")
            return 0

        def stonith(self, failingHost, **kwargs):
            method = "stonith"
            self.tracer.debug("enter stonith hook; {0}".format(locals()))
            self.tracer.debug(self.config.toString())
            # e.g. stonith of params["failed_host"]
            # e-g- set vIP active
            self.tracer.info("leave stonith hook")
            return 0

        def preTakeover(self, isForce, **kwargs):
            """Pre takeover hook."""
            method = "preTakeover"
            self.tracer.info("{0}.{1}() method called with isForce={2}".format(self.__class__.__name__, method, isForce))
            if not isForce:
                # run pre takeover code
                # run pre-check, return != 0 in case of error => will abort takeover
                return 0
            else:
                # possible force-takeover only code
                # usually nothing to do here
                return 0

        def postTakeover(self, rc, **kwargs):
            method = "postTakeover"
            """Post takeover hook."""
            self.tracer.info("{0}.{1}() method called with rc={2}".format(self.__class__.__name__, method, rc))
            if rc == 0:
                # normal takeover succeeded
                return 0
            elif rc == 1:
                # waiting for force takeover
                return 0
            elif rc == 2:
                # error, something went wrong
                return 0

        def srConnectionChanged(self, ParamDict, **kwargs):
            method = "srConnectionChanged"
            """ finally we got the srConnection hook :) """
            self.tracer.info("{0}.{1}() method called with Dict={2} (version {3}) and cib_access {4}".format(self.__class__.__name__, method, ParamDict, fhSRHookVersion, self.cib_access))
            # myHostname = socket.gethostname()
            # myDatebase = ParamDict["database"]
            mySystemStatus = ParamDict["system_status"]
            mySID = os.environ.get('SAPSYSTEMNAME')
            mysid = mySID.lower()
            myInSync = ParamDict["is_in_sync"]
            myReason = ParamDict["reason"]
            mySite = ParamDict["siteName"]
            # if self.cib_access != "all-off" and self.cib_access != "glob-off":
            if self.cib_access == "all-on" or self.cib_access == "glob-on" or self.cib_access == "site-off":
                myCMD = "sudo /usr/sbin/crm_attribute -n hana_{1}_gsh -v {0} -l reboot".format(srHookGen, mysid)
                rc = os.system(myCMD)
                myMSG = "CALLING CRM: <{0}> rc={1}".format(myCMD, rc)
                self.tracer.info("{0}.{1}() {2}\n".format(self.__class__.__name__, method, myMSG))
                self.tracer.info("{0}.{1}() Running srHookGeneration {2}, see attribute hana_{3}_gsh too\n".format(self.__class__.__name__, method, srHookGen, mysid))
            if mySystemStatus == 15:
                mySRS = "SOK"
            else:
                if myInSync:
                    # ignoring the SFAIL, because we are still in sync
                    self.tracer.info("{0}.{1}() ignoring bad SR status because of is_in_sync=True (reason={2})".format(self.__class__.__name__, method, myReason))
                    mySRS = ""
                else:
                    mySRS = "SFAIL"
            if mySRS == "":
                myMSG = "### Ignoring bad SR status because of is_in_sync=True ###"
                self.tracer.info("{0}.{1}() {2}\n".format(self.__class__.__name__, method, myMSG))
            elif mySite == "":
                myMSG = "### Ignoring bad SR status because of empty site name in call params ###"
                self.tracer.info("{0}.{1}() was called with empty site name. Ignoring call.".format(self.__class__.__name__, method))
            else:
                # if self.cib_access != "all-off" and self.cib_access != "glob-off":
                if self.cib_access == "all-on" or self.cib_access == "glob-on" or self.cib_access == "site-off":
                    # check if global Hook attribute exists
                    myCMD = "sudo /usr/sbin/crm_attribute -n hana_%s_glob_srHook -G" % (mysid)
                    rc = os.system(myCMD)
                    if rc == 0:
                        # found global Hook attribute, write both (old and new) attributes
                        # for compatibility reasons
                        myCMD = "sudo /usr/sbin/crm_attribute -n hana_{0}_glob_srHook -v {1} -t crm_config -s SAPHanaSR".format(mysid, mySRS)
                        rc = os.system(myCMD)
                        myMSG = "CALLING CRM: <{0}> rc={1}".format(myCMD, rc)
                        self.tracer.info("{0}.{1}() {2}\n".format(self.__class__.__name__, method, myMSG))

                # if self.cib_access != "all-off" and self.cib_access != "site-off":
                # if self.cib_access == "all-on" or self.cib_access == "site-on" or self.cib_access == "glob-off":
                if self.cib_access == "all-on" or self.cib_access == "site-on":
                    myCMD = "sudo /usr/sbin/crm_attribute -n hana_{0}_site_srHook_{1} -v {2} -t crm_config -s SAPHanaSR".format(mysid, mySite, mySRS)
                    rc = os.system(myCMD)
                    myMSG = "CALLING CRM: <{0}> rc={1}".format(myCMD, rc)
                    self.tracer.info("{0}.{1}() {2}\n".format(self.__class__.__name__, method, myMSG))
                    #
                    if rc != 0:
                        #
                        # FALLBACK
                        # sending attribute to the cluster failed - using fallback method and write status to a file - RA to pick-up the value during next SAPHanaController monitor operation
                        #
                        myMSG = "sending attribute to the cluster failed - using local file as fallback"
                        self.tracer.info("{0}.{1}() {2}\n".format(self.__class__.__name__, method, myMSG))
                        #
                        # cwd of hana is /hana/shared/<SID>/HDB00/<hananode> we use a relative path to cwd this gives us a <sid>adm permitted directory
                        #     however we go one level up (..) to have the file accessible for all SAP HANA swarm nodes
                        #
                        fallbackFileObject = open("../.crm_attribute.stage.{0}".format(mySite), "w")
                        fallbackFileObject.write("hana_{0}_site_srHook_{1} = {2}".format(mysid, mySite, mySRS))
                        fallbackFileObject.close()
                        #
                        # release the stage file to the original name (move is used to be atomic)
                        #      .crm_attribute.stage.<site> is renamed to .crm_attribute.<site>
                        #
                        os.rename("../.crm_attribute.stage.{0}".format(mySite), "../.crm_attribute.{0}".format(mySite))
            return 0
except NameError as e:
    print("Could not find base class ({0})".format(e))
