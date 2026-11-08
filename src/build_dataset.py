"""Hand-curated, paraphrased API-change examples based on official migration guides.
This pilot is NOT an automatically scraped or independently validated benchmark.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MIGRATIONS = [
# API_ID, pkg, older, newer, query, old guidance, new guidance, official source
('express-wildcard','express','4.21.2','5.1.0','Create a catch-all route including root requests',
 "Catch-all routing for all request paths can use app.get('/*', handler) in Express.",
 "Express 5 named wildcard matching uses app.get('/{*splat}', handler) to include the root path.",
 'https://expressjs.com/en/guide/migrating-5/'),
('express-optional','express','4.21.2','5.1.0','Define an image route with an optional extension',
 "Express route path with optional extension can use '/:file.:ext?' in app.get.",
 "Express 5 route path optional extension should use '/:file{.:ext}' in app.get.",
 'https://expressjs.com/en/guide/migrating-5/'),
('express-del','express','4.21.2','5.1.0','Register the DELETE HTTP handler for a resource',
 "An Express application supports app.del('/item', handler) as an alias for DELETE registration.",
 "Express 5 removes app.del(); register DELETE handlers with app.delete('/item', handler).",
 'https://expressjs.com/en/guide/migrating-5/'),
('express-reqparam','express','4.21.2','5.1.0','Read the id parameter provided in a route path',
 "In Express 4 req.param('id') accesses an HTTP request parameter by its name.",
 "Express 5 removes req.param(); use req.params.id for route parameters.",
 'https://expressjs.com/en/guide/migrating-5/'),
('express-sendstatus','express','4.21.2','5.1.0','Send HTTP status 204 as the response',
 "Express 4 accepts res.send(204) to send a status-only response.",
 "Express 5 removes res.send(status); use res.sendStatus(204) for a status-only response.",
 'https://expressjs.com/en/guide/migrating-5/'),
('express-redirect','express','4.21.2','5.1.0','Redirect the client to the next URL with HTTP status 301',
 "Express 4 supports res.redirect('/next', 301) with destination first.",
 "Express 5 uses res.redirect(301, '/next') with status before destination.",
 'https://expressjs.com/en/guide/migrating-5/'),
('mongoose-findcallback','mongoose','6.13.8','7.8.7','Find a user record and handle completion of the database query',
 "Mongoose 6 query functions support Model.findOne({email}, callback) and pass result to callback.",
 "Mongoose 7 no longer accepts query callbacks; use await Model.findOne({email}) or .then().",
 'https://mongoosejs.com/docs/7.x/docs/migrating_to_7.html'),
('mongoose-remove','mongoose','6.13.8','7.8.7','Delete matching database records using the model',
 "Mongoose 6 Model.remove(filter) is available for removing documents.",
 "Mongoose 7 removes Model.remove(); use Model.deleteOne(filter) or Model.deleteMany(filter).",
 'https://mongoosejs.com/docs/7.x/docs/migrating_to_7.html'),
('mongoose-update','mongoose','6.13.8','7.8.7','Update matching documents using the model method',
 "Mongoose 6 exposes Model.update(filter, update) for updating documents.",
 "Mongoose 7 removes Model.update(); use Model.updateOne or Model.updateMany.",
 'https://mongoosejs.com/docs/7.x/docs/migrating_to_7.html'),
('mongoose-objectid','mongoose','6.13.8','7.8.7','Create a BSON ObjectId from its hexadecimal string',
 "Mongoose 6 permits mongoose.Types.ObjectId(hexString) without new.",
 "Mongoose 7 requires new mongoose.Types.ObjectId(hexString) when constructing an ObjectId.",
 'https://mongoosejs.com/docs/7.x/docs/migrating_to_7.html'),
('mongoose-mapreduce','mongoose','6.13.8','7.8.7','Execute a map-reduce operation on a MongoDB model',
 "Mongoose 6 includes Model.mapReduce(options) for map-reduce operations.",
 "Mongoose 7 removes Model.mapReduce; use aggregation pipelines where applicable.",
 'https://mongoosejs.com/docs/7.x/docs/migrating_to_7.html'),
('mongoose-querydefault','mongoose','6.13.8','7.8.7','Configure whether unrecognized filter fields are stripped by default',
 "Mongoose 6 uses strictQuery true by default and strips unknown filter properties.",
 "Mongoose 7 uses strictQuery false by default and keeps unknown filter properties unless configured.",
 'https://mongoosejs.com/docs/7.x/docs/migrating_to_7.html'),
('router-history','react-router-dom','5.3.4','6.30.1','Navigate programmatically to dashboard after logging in',
 "React Router 5 uses useHistory() and history.push('/dashboard') for navigation.",
 "React Router 6 replaces useHistory with useNavigate(); call navigate('/dashboard').",
 'https://reactrouter.com/docs/en/v6/upgrading/v5'),
('router-switch','react-router-dom','5.3.4','6.30.1','Render the first matching route in a route collection',
 "React Router 5 wraps matching Route elements within a Switch component.",
 "React Router 6 uses Routes instead of Switch for route matching.",
 'https://reactrouter.com/docs/en/v6/upgrading/v5'),
('router-redirect','react-router-dom','5.3.4','6.30.1','Redirect a user to the home page from a route component',
 "React Router 5 uses the Redirect component to navigate the user.",
 "React Router 6 replaces Redirect with the Navigate component for navigation.",
 'https://reactrouter.com/docs/en/v6/upgrading/v5'),
('router-component','react-router-dom','5.3.4','6.30.1','Define a route that renders a Home component',
 "React Router 5 uses Route component={Home} or render={...} patterns.",
 "React Router 6 uses Route element={<Home />} instead of component or render props.",
 'https://reactrouter.com/docs/en/v6/upgrading/v5'),
('router-routematch','react-router-dom','5.3.4','6.30.1','Match the current URL against a route pattern using a hook',
 "React Router 5 provides useRouteMatch to match a pathname with route information.",
 "React Router 6 replaces useRouteMatch with useMatch for route matching.",
 'https://reactrouter.com/docs/en/v6/upgrading/v5'),
('router-redirectstate','react-router-dom','5.3.4','6.30.1','Redirect to a profile screen while passing navigation state',
 "React Router 5 can put state into Redirect to={{pathname:'/profile', state:{from:'login'}}}.",
 "React Router 6 passes state as a separate prop on Navigate, e.g. <Navigate to='/profile' state={{from:'login'}} />.",
 'https://reactrouter.com/docs/en/v6/upgrading/v5')
]


def make():
    documents=[]; tasks=[]
    for item in MIGRATIONS:
        key,pkg,old,new,query,old_doc,new_doc,source=item
        # Represent historical compatibility at major-boundary only, deliberately excluding unknown versions.
        for label, ver, desc in [('old',old,old_doc),('new',new,new_doc)]:
            did=f'{key}-{label}'
            documents.append(dict(id=did, api_id=key, package=pkg, version=ver,
                                  valid_versions=[ver], text=desc, source=source,
                                  provenance='author-paraphrased from linked vendor migration guide'))
            tasks.append(dict(id=f'{key}-task-{label}',api_id=key,package=pkg,
                              target_version=ver,query=query,
                              correct_doc_id=did, source=source,
                              package_json={'dependencies':{pkg:'^'+ver}},
                              package_lock={'lockfileVersion':3, 'packages':{'node_modules/'+pkg:{'version':ver}}}))
    (BASE/'data'/'documents.json').write_text(json.dumps(documents,indent=2)+'\n')
    (BASE/'data'/'tasks.json').write_text(json.dumps(tasks,indent=2)+'\n')
    return len(documents), len(tasks)

if __name__ == '__main__':
    print('docs, tasks:',make())
