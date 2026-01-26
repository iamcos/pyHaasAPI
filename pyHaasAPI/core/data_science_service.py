import pandas as pd
import numpy as np
import json
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from scipy import stats

class DataScienceService:
    """
    Advanced Data Science workflows for Haas Backtest Data.
    Handles feature extraction from parameters, importance modeling, and clustering.
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.feature_df = None
        self.importance_results = None

    def prepare_features(self, target_metric="roi_custom"):
        """
        Flattens the JSON parameters into columns and cleans the data for modeling.
        """
        if self.df.empty:
            return pd.DataFrame()

        # 1. Flatten Parameters
        all_params = []
        for p_str in self.df["parameters"]:
            try:
                all_params.append(json.loads(p_str))
            except:
                all_params.append({})
        
        flat_params = pd.DataFrame(all_params)
        
        # 2. Keep only numeric columns or columns with low cardinality (categorical)
        # For now, focus on numeric for statistical modeling
        numeric_params = flat_params.select_dtypes(include=[np.number])
        
        # 3. Merge with Target
        modeling_df = pd.concat([numeric_params, self.df[[target_metric]]], axis=1).dropna()
        
        # Remove constants (zero variance)
        modeling_df = modeling_df.loc[:, (modeling_df.var() > 0)]
        
        self.feature_df = modeling_df
        return modeling_df

    def get_feature_importance(self, target_metric="roi_custom"):
        """
        Uses Random Forest to rank which parameters influence the target metric.
        """
        if self.feature_df is None:
            self.prepare_features(target_metric)
            
        if self.feature_df.empty or len(self.feature_df.columns) < 2:
            return pd.Series()

        X = self.feature_df.drop(columns=[target_metric])
        y = self.feature_df[target_metric]
        
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(X, y)
        
        importance = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
        self.importance_results = importance
        return importance

    def get_parameter_correlations(self, target_metric="roi_custom"):
        """
        Calculates correlation matrix between parameters and the target.
        """
        if self.feature_df is None:
            self.prepare_features(target_metric)
            
        if self.feature_df.empty:
            return pd.DataFrame()

        return self.feature_df.corr()[target_metric].sort_values(ascending=False)

    def cluster_bots(self, n_clusters=5):
        """
        Groups bots into profiles based on their parameter 'DNA'.
        """
        if self.feature_df is None:
            self.prepare_features()
            
        if self.feature_df.empty:
            return []

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(self.feature_df.drop(columns=["roi_custom"], errors="ignore"))
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(X_scaled)
        
        return clusters

    def get_sensitivity_scores(self, param_name, target_metric="roi_custom"):
        """
        Simple sensitivity analysis for a specific parameter.
        Returns ROI mean and std for binned values of the parameter.
        """
        if self.feature_df is None:
            self.prepare_features(target_metric)
            
        if param_name not in self.feature_df.columns:
            return pd.DataFrame()

        # Bin the parameter into 10 groups
        self.feature_df["bin"] = pd.qcut(self.feature_df[param_name], q=10, duplicates="drop")
        stats = self.feature_df.groupby("bin")[target_metric].agg(["mean", "std", "count"])
        return stats
