import React, {useContext} from 'react';
import './App.css';
import './globals';
import './styles/styles.less';
import 'bootstrap';
import {Routes, Route} from "react-router-dom";

import PageWithSidebar from "./components/PageWithSidebar/PageWithSidebar";
import {StoresContext} from "./contexts/Stores";
import {globalMenuSettings} from "./plugins/GlobalMenuSettings";
import {globalRoutes} from "./plugins/GlobalRoutes";
import {useCurrentTimeSetupTimers} from "./util/Moment";
import Topbar from "./components/Topbar/Topbar";
import TopbarActions from "./components/TopbarActions/TopbarActions";
import Loginbar from "./components/Loginbar/Loginbar";

// import the views so that they register themselves in the plugin system
import './views/HomeView/HomeView';
import './views/BuildersView/BuildersView';
import './views/BuilderView/BuilderView';
import './views/BuildView/BuildView';
import './views/PendingBuildRequestsView/PendingBuildRequestsView';
import './views/ChangesView/ChangesView';
import './views/ChangeBuildsView/ChangeBuildsView';
import './views/MastersView/MastersView';
import './views/SchedulersView/SchedulersView';
import './views/WorkersView/WorkersView';

function App() {
  const stores = useContext(StoresContext);

  useCurrentTimeSetupTimers();

  const routeElements = globalRoutes.routes.map(config => {
    return <Route key={config.route} path={config.route} element={config.element()}/>
  });

  return (
    <PageWithSidebar menuSettings={globalMenuSettings} sidebarStore={stores.sidebar}>
      <Topbar store={stores.topbar} appTitle={globalMenuSettings.appTitle}>
        <TopbarActions store={stores.topbarActions}/>
        <Loginbar/>
      </Topbar>
      <Routes>
        {routeElements}
      </Routes>
    </PageWithSidebar>
  );
}

export default App;
