export type ArchitectureEntity = {
  id: string;
  name: string;
  path: string;
  layer: string;
};

export type ArchitectureRoute = {
  method: string;
  path: string;
  framework: string;
  file: string;
};

export type ArchitectureDependency = {
  from: string;
  to: string;
  kind: string;
};

export type ArchitectureAnalysis = {
  directories?: string[];
  entities?: ArchitectureEntity[];
  routes?: ArchitectureRoute[];
  middleware?: ArchitectureEntity[];
  controllers?: ArchitectureEntity[];
  service_entities?: ArchitectureEntity[];
  models?: ArchitectureEntity[];
  database_layers?: ArchitectureEntity[];
  dependencies?: ArchitectureDependency[];
  technologies?: string[];
  mermaid?: string;
  project_structure?: Record<string, string[]>;
  api_routes?: string[];
  database_interactions?: string[];
  major_modules?: Array<{ module: string; responsibility: string }>;
  dependency_relationships?: string[];
  request_data_flow?: string[];
};
