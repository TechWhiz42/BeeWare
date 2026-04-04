from risk_model import BeeWareRiskModel

DATA_PATH = "data/dataset.csv"

model = BeeWareRiskModel()

model.train_from_csv(DATA_PATH)
model.save("beeware_model.pkl")